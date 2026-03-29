from flask import Blueprint, request, jsonify
from models.order import Order
from models.medicine import Medicine
from database.db import db
from models.order_item import OrderItem
order_bp = Blueprint('order_bp', __name__)

@order_bp.route('/', methods=['GET'])
def get_orders():
    from models.order import Order
    orders = Order.query.all()
    return jsonify([{
    "id": o.id,
    "user_id": o.user_id,
    "customer_name": o.customer_name or 'Walk-in Customer',
    "total_price": o.total_amount,
    "status": o.status or 'completed',
    "customer_phone": o.customer_phone or '—',
    "created_at": o.created_at.isoformat() if o.created_at else None
} for o in orders])



@order_bp.route('/place', methods=['POST'])
def place_order():
    data = request.json
    items = data.get('items', [])
    if not items:
        return jsonify({"error": "No items"}), 400

    total = 0
    order = Order(
        user_id=1,
        customer_name=data.get('customer_name', 'Walk-in Customer'),
        customer_phone=data.get('customer_phone', ''),
        total_amount=0
    )
    db.session.add(order)
    db.session.flush()

    for item in items:
        medicine = Medicine.query.get(item['medicine_id'])
        if not medicine or medicine.stock < item['quantity']:
            db.session.rollback()
            return jsonify({"error": f"{medicine.name if medicine else 'Medicine'} out of stock"}), 400
        medicine.stock -= item['quantity']
        line_total = round(medicine.price * item['quantity'] * 1.18, 2)
        total += line_total
        db.session.add(OrderItem(
            order_id=order.id,
            medicine_id=medicine.id,
            medicine_name=medicine.name,
            quantity=item['quantity'],
            price=medicine.price
        ))

    order.total_amount = round(total, 2)
    db.session.commit()
    return jsonify({"message": "Order placed", "total": total})