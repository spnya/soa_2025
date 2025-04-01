from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from sqlalchemy.orm import Session
from models import Post


class PostsService:
    def __init__(self, db_session):
        self.db_session = db_session

    def create_post(self, title, description, user_id, is_private=False, tags=None):
        session = self.db_session()
        try:
            post = Post(
                title=title,
                description=description,
                user_id=user_id,
                is_private=is_private,
                tags=tags or []
            )
            session.add(post)
            session.commit()
            # Make sure to return the to_dict result directly here
            return post.to_dict(), None
        except Exception as e:
            session.rollback()
            return None, str(e)
        finally:
            session.close()

    def get_post(self, post_id, user_id):
        session = self.db_session()
        try:
            post = session.query(Post).filter(Post.id == post_id).first()

            if not post:
                return None, "Post not found"

            if post.is_private and post.user_id != user_id:
                return None, "Access denied: this post is private"

            return post.to_dict(), None
        except Exception as e:
            return None, str(e)
        finally:
            session.close()

    def update_post(self, post_id, user_id, title=None, description=None, is_private=None, tags=None):
        session = self.db_session()
        try:
            post = session.query(Post).filter(Post.id == post_id).first()

            if not post:
                return None, "Post not found"

            if post.user_id != user_id:
                return None, "Access denied: you are not the owner of this post"

            if title is not None:
                post.title = title
            if description is not None:
                post.description = description
            if is_private is not None:
                post.is_private = is_private
            if tags is not None:
                post.tags = tags

            post.updated_at = datetime.utcnow()
            session.commit()

            return post.to_dict(), None
        except Exception as e:
            session.rollback()
            return None, str(e)
        finally:
            session.close()

    def delete_post(self, post_id, user_id):
        session = self.db_session()
        try:
            post = session.query(Post).filter(Post.id == post_id).first()

            if not post:
                return False, "Post not found"

            if post.user_id != user_id:
                return False, "Access denied: you are not the owner of this post"

            session.delete(post)
            session.commit()

            return True, "Post deleted successfully"
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    def list_posts(self, page=1, per_page=10, user_id=None, tag=None):
        session = self.db_session()
        try:
            query = session.query(Post)

            if tag:
                query = query.filter(Post.tags.contains([tag]))

            if user_id:
                query = query.filter(
                    (Post.user_id == user_id) |
                    ((Post.is_private == False) & (Post.user_id != user_id))
                )
            else:
                query = query.filter(Post.is_private == False)

            total_count = query.count()
            total_pages = (total_count + per_page - 1) // per_page

            posts = query.order_by(Post.created_at.desc()) \
                .offset((page - 1) * per_page) \
                .limit(per_page) \
                .all()

            return {
                       'posts': [post.to_dict() for post in posts],
                       'total_count': total_count,
                       'page': page,
                       'total_pages': total_pages
                   }, None
        except Exception as e:
            return None, str(e)
        finally:
            session.close()