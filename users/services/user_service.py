from models import User, db
from datetime import datetime


class UserService:
    @staticmethod
    def create_user(username, password, email, **kwargs):
        """
        Создание нового пользователя
        """
        user = User(
            username=username,
            password=password,
            email=email,
            **kwargs
        )

        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_user_by_id(user_id):
        """
        Получение пользователя по ID
        """
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_username(username):
        """
        Получение пользователя по логину
        """
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_user_by_email(email):
        """
        Получение пользователя по email
        """
        return User.query.filter_by(email=email).first()

    @staticmethod
    def update_user(user, data):
        """
        Обновление данных пользователя
        """
        for key, value in data.items():
            if key != 'password' and key != 'username' and hasattr(user, key):
                setattr(user, key, value)

        user.updated_at = datetime.utcnow()
        db.session.commit()
        return user