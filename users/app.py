from flask import Flask
from flask_cors import CORS
from routes.user_routes import user_blueprint
from models import db
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

db.init_app(app)

app.register_blueprint(user_blueprint, url_prefix='/api')

@app.route('/', methods=['GET'])
def home():
    return {"message": "User Service is running", "version": "1.0.0"}

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)