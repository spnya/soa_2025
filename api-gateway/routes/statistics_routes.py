from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError, validate
import jwt
import grpc
from datetime import datetime
from functools import wraps
import statistics_pb2
import statistics_pb2_grpc
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

statistics_blueprint = Blueprint('statistics', __name__)


class PostStatsQuerySchema(Schema):
    """Схема для запроса статистики поста"""
    pass  # Пока что без дополнительных параметров


class PostDynamicsQuerySchema(Schema):
    """Схема для запроса динамики по посту"""
    start_date = fields.String(validate=validate.Regexp(r'^\d{4}-\d{2}-\d{2}$'), load_default=None)
    end_date = fields.String(validate=validate.Regexp(r'^\d{4}-\d{2}-\d{2}$'), load_default=None)


class TopPostsQuerySchema(Schema):
    """Схема для запроса топ постов"""
    metric = fields.String(
        validate=validate.OneOf(['views', 'likes', 'comments']), 
        load_default='views'
    )
    limit = fields.Integer(validate=validate.Range(min=1, max=100), load_default=10)


class TopUsersQuerySchema(Schema):
    """Схема для запроса топ пользователей"""
    metric = fields.String(
        validate=validate.OneOf(['views', 'likes', 'comments']), 
        load_default='views'
    )
    limit = fields.Integer(validate=validate.Range(min=1, max=100), load_default=10)


def token_required(f):
    """Декоратор для проверки JWT токена"""
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
            user_id = data['user_id']

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401

        return f(user_id, *args, **kwargs)

    return decorated


def get_statistics_stub():
    """Получение gRPC stub для сервиса статистики"""
    channel = grpc.insecure_channel(f"{Config.STATISTICS_SERVICE_URL}:{Config.STATISTICS_SERVICE_PORT}")
    return statistics_pb2_grpc.StatisticsServiceStub(channel)


@statistics_blueprint.route('/posts/<int:post_id>/stats', methods=['GET'])
@token_required
def get_post_stats(user_id, post_id):
    """
    Получение общей статистики по посту (просмотры, лайки, комментарии)
    """
    try:
        schema = PostStatsQuerySchema()
        params = schema.load(request.args)

        stub = get_statistics_stub()

        request_proto = statistics_pb2.GetPostStatsRequest(
            post_id=post_id
        )

        response = stub.GetPostStats(request_proto)

        if response.error:
            return jsonify({'error': response.error}), 400

        stats = {
            'post_id': response.stats.post_id,
            'views': response.stats.views,
            'likes': response.stats.likes,
            'comments': response.stats.comments
        }

        return jsonify(stats), 200

    except ValidationError as err:
        return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
    except grpc.RpcError as e:
        return jsonify({'error': f"gRPC error: {e.details()}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@statistics_blueprint.route('/posts/<int:post_id>/dynamics/views', methods=['GET'])
@token_required
def get_post_views_dynamics(user_id, post_id):
    """
    Получение динамики просмотров по посту
    """
    try:
        schema = PostDynamicsQuerySchema()
        params = schema.load(request.args)

        stub = get_statistics_stub()

        request_proto = statistics_pb2.GetPostDynamicsRequest(
            post_id=post_id,
            start_date=params.get('start_date', ''),
            end_date=params.get('end_date', '')
        )

        response = stub.GetPostViewsDynamics(request_proto)

        if response.error:
            return jsonify({'error': response.error}), 400

        dynamics = []
        for day_stats in response.dynamics:
            dynamics.append({
                'date': day_stats.date,
                'count': day_stats.count
            })

        result = {
            'post_id': post_id,
            'metric': 'views',
            'dynamics': dynamics
        }

        return jsonify(result), 200

    except ValidationError as err:
        return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
    except grpc.RpcError as e:
        return jsonify({'error': f"gRPC error: {e.details()}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@statistics_blueprint.route('/posts/<int:post_id>/dynamics/likes', methods=['GET'])
@token_required
def get_post_likes_dynamics(user_id, post_id):
    """
    Получение динамики лайков по посту
    """
    try:
        schema = PostDynamicsQuerySchema()
        params = schema.load(request.args)

        stub = get_statistics_stub()

        request_proto = statistics_pb2.GetPostDynamicsRequest(
            post_id=post_id,
            start_date=params.get('start_date', ''),
            end_date=params.get('end_date', '')
        )

        response = stub.GetPostLikesDynamics(request_proto)

        if response.error:
            return jsonify({'error': response.error}), 400

        dynamics = []
        for day_stats in response.dynamics:
            dynamics.append({
                'date': day_stats.date,
                'count': day_stats.count
            })

        result = {
            'post_id': post_id,
            'metric': 'likes',
            'dynamics': dynamics
        }

        return jsonify(result), 200

    except ValidationError as err:
        return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
    except grpc.RpcError as e:
        return jsonify({'error': f"gRPC error: {e.details()}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@statistics_blueprint.route('/posts/<int:post_id>/dynamics/comments', methods=['GET'])
@token_required
def get_post_comments_dynamics(user_id, post_id):
    """
    Получение динамики комментариев по посту
    """
    try:
        schema = PostDynamicsQuerySchema()
        params = schema.load(request.args)

        stub = get_statistics_stub()

        request_proto = statistics_pb2.GetPostDynamicsRequest(
            post_id=post_id,
            start_date=params.get('start_date', ''),
            end_date=params.get('end_date', '')
        )

        response = stub.GetPostCommentsDynamics(request_proto)

        if response.error:
            return jsonify({'error': response.error}), 400

        dynamics = []
        for day_stats in response.dynamics:
            dynamics.append({
                'date': day_stats.date,
                'count': day_stats.count
            })

        result = {
            'post_id': post_id,
            'metric': 'comments',
            'dynamics': dynamics
        }

        return jsonify(result), 200

    except ValidationError as err:
        return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
    except grpc.RpcError as e:
        return jsonify({'error': f"gRPC error: {e.details()}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@statistics_blueprint.route('/posts/top', methods=['GET'])
@token_required
def get_top_posts(user_id):
    """
    Получение топ 10 постов по количеству лайков, комментариев или просмотров
    """
    try:
        schema = TopPostsQuerySchema()
        params = schema.load(request.args)

        stub = get_statistics_stub()

        # Маппинг строковых значений в enum
        metric_map = {
            'views': statistics_pb2.GetTopPostsRequest.VIEWS,
            'likes': statistics_pb2.GetTopPostsRequest.LIKES,
            'comments': statistics_pb2.GetTopPostsRequest.COMMENTS
        }

        request_proto = statistics_pb2.GetTopPostsRequest(
            metric=metric_map[params['metric']],
            limit=params['limit']
        )

        response = stub.GetTopPosts(request_proto)

        if response.error:
            return jsonify({'error': response.error}), 400

        posts = []
        for post_stats in response.posts:
            posts.append({
                'post_id': post_stats.post_id,
                'views': post_stats.views,
                'likes': post_stats.likes,
                'comments': post_stats.comments
            })

        result = {
            'metric': params['metric'],
            'limit': params['limit'],
            'posts': posts
        }

        return jsonify(result), 200

    except ValidationError as err:
        return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
    except grpc.RpcError as e:
        return jsonify({'error': f"gRPC error: {e.details()}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@statistics_blueprint.route('/users/top', methods=['GET'])
@token_required
def get_top_users(user_id):
    """
    Получение топ 10 пользователей по количеству лайков, комментариев или просмотров
    """
    try:
        schema = TopUsersQuerySchema()
        params = schema.load(request.args)

        stub = get_statistics_stub()

        # Маппинг строковых значений в enum
        metric_map = {
            'views': statistics_pb2.GetTopUsersRequest.VIEWS,
            'likes': statistics_pb2.GetTopUsersRequest.LIKES,
            'comments': statistics_pb2.GetTopUsersRequest.COMMENTS
        }

        request_proto = statistics_pb2.GetTopUsersRequest(
            metric=metric_map[params['metric']],
            limit=params['limit']
        )

        response = stub.GetTopUsers(request_proto)

        if response.error:
            return jsonify({'error': response.error}), 400

        users = []
        for user_stats in response.users:
            users.append({
                'user_id': user_stats.user_id,
                'views': user_stats.views,
                'likes': user_stats.likes,
                'comments': user_stats.comments
            })

        result = {
            'metric': params['metric'],
            'limit': params['limit'],
            'users': users
        }

        return jsonify(result), 200

    except ValidationError as err:
        return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
    except grpc.RpcError as e:
        return jsonify({'error': f"gRPC error: {e.details()}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
