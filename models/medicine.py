from database.db import db

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)
    category = db.Column(db.String(50))
    expiry_days = db.Column(db.Integer)
    age_group = db.Column(db.String(20))