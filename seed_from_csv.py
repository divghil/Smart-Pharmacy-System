import csv
from app import app
from database.db import db
from models.medicine import Medicine

def clean_value(value, default=0):
    try:
        return float(value)
    except:
        return default

def load_data():
    with app.app_context():
        with open('medicines.csv', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            count = 0

            for row in reader:
                row = {k.strip().lower(): v for k, v in row.items()}
                if not row['medicine']:
                    continue

                med = Medicine(
                    name=row['medicine'],
                    price=clean_value(row['price'], 50),
                    stock=int(float(row['stock'])) if row['stock'] else 100,
                    category=row['category'] if row['category'] else "General",
                    expiry_days=int(float(row['expiry_days'])) if row['expiry_days'] else 365,
                    age_group=row['age_group'] if row['age_group'] else "General"
                )

                db.session.add(med)
                count += 1

            db.session.commit()
            print(f"{count} medicines imported successfully!")

if __name__ == "__main__":
    load_data()