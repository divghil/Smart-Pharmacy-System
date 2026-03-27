from flask import Blueprint, jsonify, request
from models.medicine import Medicine
from database.db import db

medicine_bp = Blueprint('medicine_bp', __name__)


# ✅ 1. Get Medicines (WITH PAGINATION + FILTERS)
@medicine_bp.route('/', methods=['GET'])
def get_medicines():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    age_group = request.args.get('age_group')

    query = Medicine.query

    # 🔹 Filter by age group (optional)
    if age_group:
        query = query.filter_by(age_group=age_group)

    medicines = query.paginate(page=page, per_page=limit)

    result = []
    for m in medicines.items:
        result.append({
            "id": m.id,
            "name": m.name,
            "price": m.price,
            "stock": m.stock,
            "category": m.category,
            "expiry_days": m.expiry_days,
            "age_group": m.age_group
        })

    return jsonify({
        "page": page,
        "total_pages": medicines.pages,
        "total_items": medicines.total,
        "data": result
    })


# ✅ 2. Add Medicine
@medicine_bp.route('/add', methods=['POST'])
def add_medicine():
    data = request.json

    med = Medicine(
        name=data['name'],
        price=data['price'],
        stock=data['stock'],
        category=data.get('category', 'General'),
        expiry_days=data.get('expiry_days', 365),
        age_group=data.get('age_group', 'General')
    )

    db.session.add(med)
    db.session.commit()

    return jsonify({"message": "Medicine added successfully"})


# ✅ 3. Low Stock Alert
@medicine_bp.route('/low-stock', methods=['GET'])
def low_stock():
    threshold = int(request.args.get('threshold', 50))

    medicines = Medicine.query.filter(Medicine.stock < threshold).all()

    result = []
    for m in medicines:
        result.append({
            "id": m.id,
            "name": m.name,
            "stock": m.stock
        })

    return jsonify(result)


# ✅ 4. Expiry Alert
@medicine_bp.route('/expiring', methods=['GET'])
def expiring_medicines():
    days = int(request.args.get('days', 30))

    medicines = Medicine.query.filter(Medicine.expiry_days < days).all()

    result = []
    for m in medicines:
        result.append({
            "id": m.id,
            "name": m.name,
            "expiry_days": m.expiry_days
        })

    return jsonify(result)


# ✅ 5. Get Single Medicine by ID
@medicine_bp.route('/<int:id>', methods=['GET'])
def get_medicine(id):
    m = Medicine.query.get(id)

    if not m:
        return jsonify({"error": "Medicine not found"}), 404

    return jsonify({
        "id": m.id,
        "name": m.name,
        "price": m.price,
        "stock": m.stock,
        "category": m.category,
        "expiry_days": m.expiry_days,
        "age_group": m.age_group
    })