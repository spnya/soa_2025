import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from posts_service import PostsService
from models import Post


class TestPostsService(unittest.TestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.db_session = MagicMock(return_value=self.session)
        self.posts_service = PostsService(self.db_session)

    def test_create_post_fixed(self):
        session = MagicMock()
        self.db_session.return_value = session

        now = datetime.utcnow()
        expected_result = {
            'id': 1,
            'title': 'Test Post',
            'description': 'Test Description',
            'user_id': 1,
            'is_private': False,
            'tags': ['test'],
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }

        mock_post = MagicMock()
        mock_post.id = 1
        mock_post.title = 'Test Post'
        mock_post.description = 'Test Description'
        mock_post.user_id = 1
        mock_post.is_private = False
        mock_post.tags = ['test']
        mock_post.created_at = now
        mock_post.updated_at = now
        mock_post.to_dict.return_value = expected_result

        with patch('posts_service.Post', return_value=mock_post):
            result, error = self.posts_service.create_post(
                title='Test Post',
                description='Test Description',
                user_id=1,
                is_private=False,
                tags=['test']
            )

            self.assertEqual(result, expected_result)
            self.assertIsNone(error)
            session.add.assert_called_once()
            session.commit.assert_called_once()

    def test_create_post_error(self):
        # For the error test, we don't need to worry about the post's attributes
        # since the exception will be raised before they're used
        mock_post = MagicMock(spec=Post)

        # Configure session to raise an exception on commit
        self.session.commit.side_effect = Exception("Database error")

        with patch('models.Post', return_value=mock_post):
            # This should catch the exception and return an error
            result, error = self.posts_service.create_post(
                title='Test Post',
                description='Test Description',
                user_id=1
            )

            # Check that we got the expected error response
            self.assertIsNone(result)
            self.assertIsNotNone(error)
            self.assertIn("Database error", error)
            self.session.rollback.assert_called_once()

    def test_get_post(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.title = 'Test Post'
        mock_post.description = 'Test Description'
        mock_post.user_id = 1
        mock_post.is_private = False
        mock_post.tags = ['test']
        mock_post.created_at = datetime.utcnow()
        mock_post.updated_at = datetime.utcnow()

        mock_post.to_dict.return_value = {
            'id': mock_post.id,
            'title': mock_post.title,
            'description': mock_post.description,
            'user_id': mock_post.user_id,
            'is_private': mock_post.is_private,
            'tags': mock_post.tags,
            'created_at': mock_post.created_at.isoformat(),
            'updated_at': mock_post.updated_at.isoformat()
        }

        self.session.query.return_value.filter.return_value.first.return_value = mock_post

        result, error = self.posts_service.get_post(post_id=1, user_id=1)

        self.assertIsNotNone(result)
        self.assertIsNone(error)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['title'], 'Test Post')

    def test_get_private_post_denied(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.is_private = True
        mock_post.user_id = 1

        self.session.query.return_value.filter.return_value.first.return_value = mock_post

        result, error = self.posts_service.get_post(post_id=1, user_id=2)

        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIn("Access denied", error)

    def test_update_post(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.title = 'Original Title'
        mock_post.description = 'Original Description'
        mock_post.user_id = 1
        mock_post.is_private = False
        mock_post.tags = ['original']
        mock_post.created_at = datetime.utcnow()
        mock_post.updated_at = datetime.utcnow()

        mock_post.to_dict.return_value = {
            'id': mock_post.id,
            'title': 'Updated Title',
            'description': mock_post.description,
            'user_id': mock_post.user_id,
            'is_private': mock_post.is_private,
            'tags': mock_post.tags,
            'created_at': mock_post.created_at.isoformat(),
            'updated_at': mock_post.updated_at.isoformat()
        }

        self.session.query.return_value.filter.return_value.first.return_value = mock_post

        result, error = self.posts_service.update_post(
            post_id=1,
            user_id=1,
            title='Updated Title'
        )

        self.assertIsNotNone(result)
        self.assertIsNone(error)
        self.assertEqual(result['title'], 'Updated Title')
        self.session.commit.assert_called_once()

    def test_update_post_not_owner(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.user_id = 1

        self.session.query.return_value.filter.return_value.first.return_value = mock_post

        result, error = self.posts_service.update_post(
            post_id=1,
            user_id=2,
            title='Updated Title'
        )

        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIn("Access denied", error)

    def test_delete_post(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.user_id = 1

        self.session.query.return_value.filter.return_value.first.return_value = mock_post

        success, message = self.posts_service.delete_post(post_id=1, user_id=1)

        self.assertTrue(success)
        self.assertIn("successfully", message)
        self.session.delete.assert_called_once_with(mock_post)
        self.session.commit.assert_called_once()

    def test_delete_post_not_found(self):
        self.session.query.return_value.filter.return_value.first.return_value = None

        success, message = self.posts_service.delete_post(post_id=999, user_id=1)

        self.assertFalse(success)
        self.assertIn("not found", message)

    def test_list_posts(self):
        mock_post1 = MagicMock(spec=Post)
        mock_post1.id = 1
        mock_post1.title = 'Post 1'
        mock_post1.description = 'Description 1'
        mock_post1.user_id = 1
        mock_post1.is_private = False
        mock_post1.tags = ['tag1']
        mock_post1.created_at = datetime.utcnow()
        mock_post1.updated_at = datetime.utcnow()

        mock_post1.to_dict.return_value = {
            'id': mock_post1.id,
            'title': mock_post1.title,
            'description': mock_post1.description,
            'user_id': mock_post1.user_id,
            'is_private': mock_post1.is_private,
            'tags': mock_post1.tags,
            'created_at': mock_post1.created_at.isoformat(),
            'updated_at': mock_post1.updated_at.isoformat()
        }

        mock_post2 = MagicMock(spec=Post)
        mock_post2.id = 2
        mock_post2.title = 'Post 2'
        mock_post2.description = 'Description 2'
        mock_post2.user_id = 2
        mock_post2.is_private = False
        mock_post2.tags = ['tag2']
        mock_post2.created_at = datetime.utcnow()
        mock_post2.updated_at = datetime.utcnow()

        mock_post2.to_dict.return_value = {
            'id': mock_post2.id,
            'title': mock_post2.title,
            'description': mock_post2.description,
            'user_id': mock_post2.user_id,
            'is_private': mock_post2.is_private,
            'tags': mock_post2.tags,
            'created_at': mock_post2.created_at.isoformat(),
            'updated_at': mock_post2.updated_at.isoformat()
        }

        self.session.query.return_value.filter.return_value.count.return_value = 2
        self.session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_post1, mock_post2]

        result, error = self.posts_service.list_posts(page=1, per_page=10)

        self.assertIsNotNone(result)
        self.assertIsNone(error)
        self.assertEqual(len(result['posts']), 2)
        self.assertEqual(result['total_count'], 2)
        self.assertEqual(result['page'], 1)


if __name__ == '__main__':
    unittest.main()
