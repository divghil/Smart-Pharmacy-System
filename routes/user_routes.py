from flask import Blueprint, request, jsonify
from models.user import User
from database.db import db

user_bp = Blueprint('user_bp', __name__)
@user_bp.route('/', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "name": u.name,
        "phone": u.phone,
        "email": u.email,
        "role": u.role
    } for u in users])

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.json

    user = User(
        name=data['name'],
        email=data['email'],
        password=data['password'],
        phone=data.get('phone', ''),
        role=data.get('role', 'customer')
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered"})