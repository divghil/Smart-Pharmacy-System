from flask import Flask, render_template
from config import Config
from database.db import db
from routes.user_routes import user_bp
from routes.medicine_routes import medicine_bp
from routes.order_routes import order_bp
from flask_cors import CORS
from routes.ml_routes import ml_bp

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/*": {"origins": "*"}})
db.init_app(app)



# Register Blueprints
app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(medicine_bp, url_prefix='/medicines')
app.register_blueprint(order_bp, url_prefix='/orders')
app.register_blueprint(ml_bp, url_prefix='/ml')

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)