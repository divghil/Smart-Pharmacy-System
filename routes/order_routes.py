from flask import Blueprint, request, jsonify
from models.order import Order
from models.medicine import Medicine
from database.db import db

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

    medicine = Medicine.query.get(data['medicine_id'])

    if not medicine or medicine.stock < data['quantity']:
        return jsonify({"error": "Out of stock"}), 400

    total = medicine.price * data['quantity']

    # reduce stock
    medicine.stock -= data['quantity']

    order = Order(
        user_id=data['user_id'],
        customer_name=data.get('customer_name', 'Walk-in Customer'),
        customer_phone=data.get('customer_phone', ''),
        total_amount=total
    )

    db.session.add(order)
    db.session.commit()

    return jsonify({"message": "Order placed", "total": total})