from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from sqlalchemy.orm import Session
from models import Post, PostView, PostLike, Comment
from kafka_producer import EventProducer
from config import Config
import logging

class PostsService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.event_producer = EventProducer(Config.KAFKA_BOOTSTRAP_SERVERS)

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
            return post.to_dict(), None
        except Exception as e:
            session.rollback()
            logging.error(f"Error creating post: {str(e)}")
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
            logging.error(f"Error getting post: {str(e)}")
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
            logging.error(f"Error updating post: {str(e)}")
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
            logging.error(f"Error deleting post: {str(e)}")
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
            logging.error(f"Error listing posts: {str(e)}")
            return None, str(e)
        finally:
            session.close()
            
    def view_post(self, post_id, user_id):
        session = self.db_session()
        try:
            post = session.query(Post).filter(Post.id == post_id).first()
            
            if not post:
                return False, "Post not found"
                
            if post.is_private and post.user_id != user_id:
                return False, "Access denied: this post is private"
                
            existing_view = session.query(PostView).filter(
                PostView.post_id == post_id,
                PostView.user_id == user_id
            ).first()
            
            if not existing_view:
                view = PostView(
                    post_id=post_id,
                    user_id=user_id
                )
                session.add(view)
                session.commit()
                
                # Send event to Kafka
                self.event_producer.send_view_event(
                    user_id=user_id,
                    post_id=post_id
                )
                
            return True, "Post viewed successfully"
        except Exception as e:
            session.rollback()
            logging.error(f"Error viewing post: {str(e)}")
            return False, str(e)
        finally:
            session.close()
    
    def like_post(self, post_id, user_id):
        session = self.db_session()
        try:
            post = session.query(Post).filter(Post.id == post_id).first()
            
            if not post:
                return False, "Post not found"
                
            if post.is_private and post.user_id != user_id:
                return False, "Access denied: this post is private"
                
            existing_like = session.query(PostLike).filter(
                PostLike.post_id == post_id,
                PostLike.user_id == user_id
            ).first()
            
            if existing_like:
                session.delete(existing_like)
                message = "Post unliked successfully"
            else:
                like = PostLike(
                    post_id=post_id,
                    user_id=user_id
                )
                session.add(like)
                message = "Post liked successfully"
                
                self.event_producer.send_like_event(
                    user_id=user_id,
                    post_id=post_id
                )
            
            session.commit()
            return True, message
        except Exception as e:
            session.rollback()
            logging.error(f"Error liking post: {str(e)}")
            return False, str(e)
        finally:
            session.close()
    
    def create_comment(self, post_id, user_id, content):
        session = self.db_session()
        try:
            post = session.query(Post).filter(Post.id == post_id).first()
            
            if not post:
                return None, "Post not found"
                
            if post.is_private and post.user_id != user_id:
                return None, "Access denied: this post is private"
                
            comment = Comment(
                post_id=post_id,
                user_id=user_id,
                content=content
            )
            
            session.add(comment)
            session.commit()
            
            self.event_producer.send_comment_event(
                user_id=user_id,
                post_id=post_id,
                comment_id=comment.id
            )
            
            return comment.to_dict(), None
        except Exception as e:
            session.rollback()
            logging.error(f"Error creating comment: {str(e)}")
            return None, str(e)
        finally:
            session.close()
    
    def list_comments(self, post_id, page=1, per_page=10):
        session = self.db_session()
        try:
            post = session.query(Post).filter(Post.id == post_id).first()
            if not post:
                return None, "Post not found"
                
            query = session.query(Comment).filter(Comment.post_id == post_id)
            
            total_count = query.count()
            total_pages = (total_count + per_page - 1) // per_page if per_page > 0 else 0
            
            comments = query.order_by(Comment.created_at.desc()) \
                .offset((page - 1) * per_page) \
                .limit(per_page) \
                .all()
                
            return {
                'comments': [comment.to_dict() for comment in comments],
                'total_count': total_count,
                'page': page,
                'total_pages': total_pages
            }, None
        except Exception as e:
            logging.error(f"Error listing comments: {str(e)}")
            return None, str(e)
        finally:
            session.close()
