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
        "total_price": o.total_amount,
        "status": getattr(o, 'status', 'completed')
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
        total_amount=total
    )

    db.session.add(order)
    db.session.commit()

    return jsonify({"message": "Order placed", "total": total})