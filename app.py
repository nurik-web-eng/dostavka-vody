import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import vk_api

app = Flask(__name__, static_folder='static')
CORS(app)

# ========== НАСТРОЙКИ VK ==========
# Замени на свои данные!
VK_TOKEN = 'vk1.a.CMOIYEJeU19yaaA9JvXjyWiZUM6eQxkUwRwblGjfsJgT9Ik9MonA_JccVuUQ0GAHlGSi2ovpWD26OYdwLc9c522d-bZ-rWDf--WbySXgBczC8BjTcQHNfNg-a4_q1STCnkQqrDFtfCzUIpcLikH5-F0b5Pa0tsACgDeuBB_hKSCtWJ6qjZVJ8NIYJfTese8T5bMKMPPcy001ksNKmXPUag'      # Токен сообщества VK
VK_GROUP_ID = 241042943                  # ID сообщества (число, без минуса)
ADMIN_VK_ID = 838874588                  # Твой VK ID (кому слать уведомления)
# ===================================

# Инициализация VK
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# Хранилище заказов (в памяти)
orders = []

def send_vk_notification(order):
    """Отправка уведомления о заказе в VK"""
    try:
        # Формируем список товаров
        items_text = ""
        for item in order['items']:
            items_text += f"• {item['name']} ({item['type']}): {item['quantity']} шт.\n"

        # Текст сообщения
        message = f"""🔔 НОВЫЙ ЗАКАЗ #{order['id']}

 Клиент: {order['name']}
 Телефон: {order['phone']}
 Адрес: ул. Испытателей, {order['house']}, кв. {order['apartment']}

📦 Товары:
{items_text}
💳 Оплата: {order['payment']}
📝 Комментарий: {order['comment']}
💰 Итого: {order['total']}₽
🕐 Время: {order['timestamp']}"""

        # Отправляем администратору
        vk.messages.send(
            user_id=ADMIN_VK_ID,
            message=message,
            random_id=0
        )

        print(f"✅ Уведомление отправлено в VK")
        return True

    except Exception as e:
        print(f"❌ Ошибка отправки в VK: {e}")
        return False

@app.route('/')
def index():
    """Главная страница"""
    return app.send_static_file('index.html')

@app.route('/api/order', methods=['POST'])
def create_order():
    """Создание нового заказа"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Нет данных'}), 400

        # Проверка обязательных полей
        required_fields = ['name', 'phone', 'house', 'apartment', 'items', 'total', 'payment']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Отсутствует поле: {field}'}), 400

        # Создаем заказ
        order = {
            'id': len(orders) + 1,
            'timestamp': (datetime.utcnow() + timedelta(hours=5)).strftime('%d.%m.%Y %H:%M'),
            'name': data['name'],
            'phone': data['phone'],
            'house': data['house'],
            'apartment': data['apartment'],
            'payment': data['payment'],
            'comment': data.get('comment', 'Не указан'),
            'items': data['items'],
            'total': data['total'],
            'status': 'new'
        }

        orders.append(order)

        # Вывод в консоль
        print(f"\n{'='*50}")
        print(f"🆕 НОВЫЙ ЗАКАЗ #{order['id']}")
        print(f"{'='*50}")
        print(f" Клиент: {order['name']}")
        print(f"📞 Телефон: {order['phone']}")
        print(f"📍 Адрес: ул. Испытателей, {order['house']}, кв. {order['apartment']}")
        print(f"💳 Оплата: {order['payment']}")
        print(f"📦 Товары:")
        for item in order['items']:
            print(f"   - {item['name']} ({item['type']}): {item['quantity']} шт. × {item['price']}₽")
        print(f" Итого: {order['total']}₽")
        print(f"{'='*50}\n")

        # Отправляем уведомление в VK
        send_vk_notification(order)

        return jsonify({
            'success': True,
            'message': 'Заказ успешно создан',
            'order_id': order['id']
        }), 201

    except Exception as e:
        print(f"❌ Ошибка при создании заказа: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Получить все заказы (для админки)"""
    return jsonify({
        'orders': orders,
        'total': len(orders)
    }), 200

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Получить конкретный заказ"""
    for order in orders:
        if order['id'] == order_id:
            return jsonify(order), 200
    return jsonify({'error': 'Заказ не найден'}), 404

if __name__ == '__main__':
    print("🚰 Сервер доставки воды запущен!")
    print("📍 http://localhost:5000")
    print(" Уведомления отправляются в VK")
  
    port = int(os.environ.get("PORT", 8080))
    
    # На Railway debug должен быть False, чтобы не вешались логи
    app.run(host='0.0.0.0', port=port, debug=False)
