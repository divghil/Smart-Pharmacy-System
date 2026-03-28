from database.db import db
from datetime import datetime

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    customer_name = db.Column(db.String(100), default='Walk-in Customer')
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer_phone = db.Column(db.String(15), default='')