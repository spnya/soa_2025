from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError, validate
import jwt
from datetime import datetime, timedelta
from functools import wraps
from models import User, db
from config import Config
from email_validator import validate_email, EmailNotValidError
from kafka_producer import EventProducer
import logging

user_blueprint = Blueprint('users', __name__)
event_producer = EventProducer(Config.KAFKA_BOOTSTRAP_SERVERS)


class UserRegistrationSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=3, max=50))
    password = fields.String(required=True, validate=validate.Length(min=8, max=100))
    email = fields.Email(required=True)


class UserLoginSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)


class ProfileUpdateSchema(Schema):
    first_name = fields.String(validate=validate.Length(max=50))
    last_name = fields.String(validate=validate.Length(max=50))
    birth_date = fields.Date()
    email = fields.Email()
    phone_number = fields.String(validate=validate.Length(max=20))
    address = fields.String(validate=validate.Length(max=255))


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()

            if not current_user:
                return jsonify({'error': 'Invalid token. User not found!'}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@user_blueprint.route('/users/register', methods=['POST'])
def register():
    try:
        schema = UserRegistrationSchema()
        data = schema.load(request.json)

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Пользователь с таким логином уже существует'}), 409

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Пользователь с таким email уже существует'}), 409

        new_user = User(
            username=data['username'],
            password=data['password'],
            email=data['email']
        )

        db.session.add(new_user)
        db.session.commit()

        # Send user registration event to Kafka
        if event_producer.send_user_registration_event(new_user.id):
            logging.info(f"User registration event sent for user_id: {new_user.id}")
        else:
            logging.error(f"Failed to send user registration event for user_id: {new_user.id}")

        return jsonify({
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'created_at': new_user.created_at.isoformat()
        }), 201

    except ValidationError as err:
        return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
    except Exception as e:
        logging.error(f"Error during user registration: {str(e)}")
        return jsonify({'error': str(e)}), 500


@user_blueprint.route('/users/login', methods=['POST'])
def login():
    try:
        schema = UserLoginSchema()
        data = schema.load(request.json)

        user = User.query.filter_by(username=data['username']).first()

        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Неверный логин или пароль'}), 401

        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
        }, Config.JWT_SECRET_KEY, algorithm="HS256")

        return jsonify({
            'access_token': token,
            'user_id': user.id,
            'username': user.username
        }), 200

    except ValidationError as err:
        return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
    except Exception as e:
        logging.error(f"Error during user login: {str(e)}")
        return jsonify({'error': str(e)}), 500


@user_blueprint.route('/users/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify(current_user.to_dict()), 200


@user_blueprint.route('/users/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    try:
        schema = ProfileUpdateSchema()
        data = schema.load(request.json)

        if 'first_name' in data:
            current_user.first_name = data['first_name']
        if 'last_name' in data:
            current_user.last_name = data['last_name']
        if 'birth_date' in data:
            current_user.birth_date = data['birth_date']
        if 'email' in data and data['email'] != current_user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Пользователь с таким email уже существует'}), 409
            current_user.email = data['email']
        if 'phone_number' in data:
            current_user.phone_number = data['phone_number']
        if 'address' in data:
            current_user.address = data['address']

        current_user.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify(current_user.to_dict()), 200

    except ValidationError as err:
        return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
    except Exception as e:
        logging.error(f"Error during profile update: {str(e)}")
        return jsonify({'error': str(e)}), 500