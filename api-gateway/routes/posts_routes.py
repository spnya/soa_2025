from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError, validate
import jwt
import grpc
from datetime import datetime
from functools import wraps
import posts_pb2
import posts_pb2_grpc
from config import Config

posts_blueprint = Blueprint('posts', __name__)


class PostCreateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(required=True)
    is_private = fields.Boolean(missing=False)
    tags = fields.List(fields.String(), missing=[])


class PostUpdateSchema(Schema):
    title = fields.String(validate=validate.Length(min=1, max=255))
    description = fields.String()
    is_private = fields.Boolean()
    tags = fields.List(fields.String())


class PaginationSchema(Schema):
    page = fields.Integer(missing=1, validate=validate.Range(min=1))
    per_page = fields.Integer(missing=10, validate=validate.Range(min=1, max=100))
    tag = fields.String(missing=None)


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
            user_id = data['user_id']

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401

        return f(user_id, *args, **kwargs)

    return decorated


def get_posts_stub():
    channel = grpc.insecure_channel(f"{Config.POSTS_SERVICE_URL}:{Config.POSTS_SERVICE_PORT}")
    return posts_pb2_grpc.PostServiceStub(channel)


@posts_blueprint.route('/posts', methods=['POST'])
@token_required
def create_post(user_id):
    try:
        schema = PostCreateSchema()
        data = schema.load(request.json)

        stub = get_posts_stub()

        request_proto = posts_pb2.CreatePostRequest(
            title=data['title'],
            description=data['description'],
            user_id=user_id,
            is_private=data['is_private'],
            tags=data['tags']
        )

        response = stub.CreatePost(request_proto)

        if response.error:
            return jsonify({'error': response.error}), 400

        post = {
            'id': response.post.id,
            'title': response.post.title,
            'description': response.post.description,
            'user_id': response.post.user_id,
            'is_private': response.post.is_private,
            'tags': list(response.post.tags),
            'created_at': response.post.created_at,
            'updated_at': response.post.updated_at
        }

        return jsonify(post), 201

    except ValidationError as err:
        return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
    except grpc.RpcError as e:
        return jsonify({'error': f"gRPC error: {e.details()}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@posts_blueprint.route('/posts/<int:post_id>', methods=['GET'])
@token_required
def get_post(user_id, post_id):
    try:
        stub = get_posts_stub()

        request_proto = posts_pb2.GetPostRequest(
            post_id=post_id,
            user_id=user_id
        )

        response = stub.GetPost(request_proto)

        if response.error:
            if "not found" in response.error:
                return jsonify({'error': response.error}), 404
            elif "Access denied" in response.error:
                return jsonify({'error': response.error}), 403
            else:
                return jsonify({'error': response.error}), 400

        post = {
            'id': response.post.id,
            'title': response.post.title,
            'description': response.post.description,
            'user_id': response.post.user_id,
            'is_private': response.post.is_private,
            'tags': list(response.post.tags),
            'created_at': response.post.created_at,
            'updated_at': response.post.updated_at
        }

        return jsonify(post), 200

    except grpc.RpcError as e:
        return jsonify({'error': f"gRPC error: {e.details()}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@posts_blueprint.route('/posts/<int:post_id>', methods=['PUT'])
@token_required
def update_post(user_id, post_id):
    try:
        schema = PostUpdateSchema()
        data = schema.load(request.json)

        stub = get_posts_stub()

        request_proto = posts_pb2.UpdatePostRequest(
            post_id=post_id,
            user_id=user_id,
            title=data.get('title', ''),
            description=data.get('description', ''),
            is_private=data.get('is_private', False),
            tags=data.get('tags', [])
        )

        response = stub.UpdatePost(request_proto)

        if response.error:
            if "not found" in response.error:
                return jsonify({'error': response.error}), 404
            elif "Access denied" in response.error:
                return jsonify({'error': response.error}), 403
            else:
                return jsonify({'error': response.error}), 400

        post = {
            'id': response.post.id,
            'title': response.post.title,
            'description': response.post.description,
            'user_id': response.post.user_id,
            'is_private': response.post.is_private,
            'tags': list(response.post.tags),
            'created_at': response.post.created_at,
            'updated_at': response.post.updated_at
        }

        return jsonify(post), 200

    except ValidationError as err:
        return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
    except grpc.RpcError as e:
        return jsonify({'error': f"gRPC error: {e.details()}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@posts_blueprint.route('/posts/<int:post_id>', methods=['DELETE'])
@token_required
def delete_post(user_id, post_id):
    try:
        stub = get_posts_stub()

        request_proto = posts_pb2.DeletePostRequest(
            post_id=post_id,
            user_id=user_id
        )

        response = stub.DeletePost(request_proto)

        if not response.success:
            if "not found" in response.message:
                return jsonify({'error': response.message}), 404
            elif "Access denied" in response.message:
                return jsonify({'error': response.message}), 403
            else:
                return jsonify({'error': response.message}), 400

        return jsonify({'message': response.message}), 200

    except grpc.RpcError as e:
        return jsonify({'error': f"gRPC error: {e.details()}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@posts_blueprint.route('/posts', methods=['GET'])
@token_required
def list_posts(user_id):
    try:
        schema = PaginationSchema()
        params = schema.load(request.args)

        stub = get_posts_stub()

        request_proto = posts_pb2.ListPostsRequest(
            page=params['page'],
            per_page=params['per_page'],
            user_id=user_id,
            tag=params['tag'] or ""
        )

        response = stub.ListPosts(request_proto)

        posts = []
        for post in response.posts:
            posts.append({
                'id': post.id,
                'title': post.title,
                'description': post.description,
                'user_id': post.user_id,
                'is_private': post.is_private,
                'tags': list(post.tags),
                'created_at': post.created_at,
                'updated_at': post.updated_at
            })

        result = {
            'posts': posts,
            'total_count': response.total_count,
            'page': response.page,
            'total_pages': response.total_pages
        }

        return jsonify(result), 200

    except ValidationError as err:
        return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
    except grpc.RpcError as e:
        return jsonify({'error': f"gRPC error: {e.details()}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500