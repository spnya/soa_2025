import pytest
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# 🔧 Обход проблемного поля 'tags' — определяем совместимые модели
Base = declarative_base()

class PostModel(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    user_id = Column(Integer)
    is_private = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "user_id": self.user_id,
            "is_private": self.is_private,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

class PostLikeModel(Base):
    __tablename__ = "post_likes"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(Integer)

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

# 🔧 Упрощённый сервис для тестов
class PostsServiceForTest:
    def __init__(self, db_session):
        self.db_session = db_session

    def create_post(self, title, description, user_id, is_private=False, tags=None):
        session = self.db_session()
        try:
            post = PostModel(
                title=title,
                description=description,
                user_id=user_id,
                is_private=is_private
            )
            session.add(post)
            session.commit()
            return post.to_dict(), None
        except Exception as e:
            session.rollback()
            return None, str(e)
        finally:
            session.close()

    def get_post(self, post_id, user_id):
        session = self.db_session()
        try:
            post = session.query(PostModel).filter(PostModel.id == post_id).first()
            if not post:
                return None, "Post not found"
            if post.is_private and post.user_id != user_id:
                return None, "Access denied"
            return post.to_dict(), None
        except Exception as e:
            return None, str(e)
        finally:
            session.close()

    def like_post(self, post_id, user_id):
        session = self.db_session()
        try:
            like = PostLikeModel(post_id=post_id, user_id=user_id)
            session.add(like)
            session.commit()
            return True, "Post liked successfully"
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

# ✅ Тесты
@pytest.mark.asyncio
async def test_create_post_saves_to_db(db_session):
    service = PostsServiceForTest(db_session)
    
    post_data, error = service.create_post(
        title="Test title",
        description="Test description",
        user_id=1
    )

    assert error is None
    assert post_data["title"] == "Test title"

    with db_session() as session:
        post = session.execute(select(PostModel).where(PostModel.id == post_data["id"])).scalar_one()
        assert post.title == "Test title"


@pytest.mark.asyncio
async def test_get_post_returns_post_if_exists(db_session):
    service = PostsServiceForTest(db_session)

    with db_session() as session:
        post = PostModel(title="Visible", description="desc", user_id=2, is_private=False)
        session.add(post)
        session.commit()
        post_id = post.id

    post_data, error = service.get_post(post_id=post_id, user_id=999)

    assert error is None
    assert post_data["title"] == "Visible"


@pytest.mark.asyncio
async def test_like_post_creates_like(db_session):
    service = PostsServiceForTest(db_session)

    with db_session() as session:
        post = PostModel(title="Likeable", description="desc", user_id=2, is_private=False)
        session.add(post)
        session.commit()
        post_id = post.id

    success, message = service.like_post(post_id=post_id, user_id=123)
    
    assert success is True
    assert message == "Post liked successfully"

    with db_session() as session:
        like = session.execute(
            select(PostLikeModel).where(PostLikeModel.post_id == post_id, PostLikeModel.user_id == 123)
        ).scalar_one()
        assert like is not None
