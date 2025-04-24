import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from posts_service import PostsService
from models import Post, PostView, PostLike, Comment


class TestPostInteractions(unittest.TestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.db_session = MagicMock(return_value=self.session)
        
        self.event_producer_patch = patch('posts_service.EventProducer')
        self.mock_event_producer = self.event_producer_patch.start()
        self.mock_event_producer_instance = self.mock_event_producer.return_value
        
        self.posts_service = PostsService(self.db_session)
        
    def tearDown(self):
        self.event_producer_patch.stop()

    def test_view_post(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.user_id = 1
        mock_post.is_private = False
        
        query_post = MagicMock()
        filter_post = MagicMock()
        query_post.filter.return_value = filter_post
        filter_post.first.return_value = mock_post
        
        query_view = MagicMock()
        filter_view1 = MagicMock()
        filter_view2 = MagicMock()
        query_view.filter.return_value = filter_view1
        filter_view1.filter.return_value = filter_view2
        filter_view2.first.return_value = None
        
        def query_side_effect(model):
            if model == Post:
                return query_post
            elif model == PostView:
                return query_view
            return MagicMock()
            
        self.session.query.side_effect = query_side_effect
        
        success, message = self.posts_service.view_post(post_id=1, user_id=2)
        
        self.assertTrue(success)
        self.assertIn("viewed successfully", message)

    def test_view_post_already_viewed(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.user_id = 1
        mock_post.is_private = False
        
        query_post = MagicMock()
        filter_post = MagicMock()
        query_post.filter.return_value = filter_post
        filter_post.first.return_value = mock_post
        
        mock_view = MagicMock(spec=PostView)
        query_view = MagicMock()
        filter_view1 = MagicMock()
        filter_view2 = MagicMock()
        query_view.filter.return_value = filter_view1
        filter_view1.filter.return_value = filter_view2
        filter_view2.first.return_value = mock_view
        
        def query_side_effect(model):
            if model == Post:
                return query_post
            elif model == PostView:
                return query_view
            return MagicMock()
            
        self.session.query.side_effect = query_side_effect
        
        success, message = self.posts_service.view_post(post_id=1, user_id=2)
        
        self.assertTrue(success)
        self.assertIn("viewed successfully", message)
        self.session.add.assert_not_called()
        self.session.commit.assert_not_called()
        self.mock_event_producer_instance.send_view_event.assert_not_called()

    def test_view_private_post_denied(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.user_id = 1
        mock_post.is_private = True
        
        query = MagicMock()
        filter_result = MagicMock()
        query.filter.return_value = filter_result
        filter_result.first.return_value = mock_post
        
        self.session.query.return_value = query
        
        success, message = self.posts_service.view_post(post_id=1, user_id=2)
        
        self.assertFalse(success)
        self.assertIn("Access denied", message)
        self.session.add.assert_not_called()
        self.session.commit.assert_not_called()
        self.mock_event_producer_instance.send_view_event.assert_not_called()

    def test_view_post_not_found(self):
        query = MagicMock()
        filter_result = MagicMock()
        query.filter.return_value = filter_result
        filter_result.first.return_value = None
        
        self.session.query.return_value = query
        
        success, message = self.posts_service.view_post(post_id=999, user_id=2)
        
        self.assertFalse(success)
        self.assertIn("not found", message)
        self.session.add.assert_not_called()
        self.session.commit.assert_not_called()
        self.mock_event_producer_instance.send_view_event.assert_not_called()

    def test_like_post(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.user_id = 1
        mock_post.is_private = False
        
        query_post = MagicMock()
        filter_post = MagicMock()
        query_post.filter.return_value = filter_post
        filter_post.first.return_value = mock_post
        
        query_like = MagicMock()
        filter_like1 = MagicMock()
        filter_like2 = MagicMock()
        query_like.filter.return_value = filter_like1
        filter_like1.filter.return_value = filter_like2
        filter_like2.first.return_value = None
        
        def query_side_effect(model):
            if model == Post:
                return query_post
            elif model == PostLike:
                return query_like
            return MagicMock()
            
        self.session.query.side_effect = query_side_effect
        
        success, message = self.posts_service.like_post(post_id=1, user_id=2)
        
        self.assertTrue(success)
        self.assertIn("liked successfully", message)

    def test_unlike_post(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.user_id = 1
        mock_post.is_private = False
        
        query_post = MagicMock()
        filter_post = MagicMock()
        query_post.filter.return_value = filter_post
        filter_post.first.return_value = mock_post
        
        mock_like = MagicMock(spec=PostLike)
        query_like = MagicMock()
        filter_like1 = MagicMock()
        filter_like2 = MagicMock()
        query_like.filter.return_value = filter_like1
        filter_like1.filter.return_value = filter_like2
        filter_like2.first.return_value = mock_like
        
        def query_side_effect(model):
            if model == Post:
                return query_post
            elif model == PostLike:
                return query_like
            return MagicMock()
            
        self.session.query.side_effect = query_side_effect
        
        success, message = self.posts_service.like_post(post_id=1, user_id=2)
        
        self.assertTrue(success)
        self.assertIn("unliked successfully", message)

    def test_like_private_post_denied(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.user_id = 1
        mock_post.is_private = True
        
        query = MagicMock()
        filter_result = MagicMock()
        query.filter.return_value = filter_result
        filter_result.first.return_value = mock_post
        
        self.session.query.return_value = query
        
        success, message = self.posts_service.like_post(post_id=1, user_id=2)
        
        self.assertFalse(success)
        self.assertIn("Access denied", message)
        self.session.add.assert_not_called()
        self.session.commit.assert_not_called()
        self.mock_event_producer_instance.send_like_event.assert_not_called()

    def test_like_post_not_found(self):
        query = MagicMock()
        filter_result = MagicMock()
        query.filter.return_value = filter_result
        filter_result.first.return_value = None
        
        self.session.query.return_value = query
        
        success, message = self.posts_service.like_post(post_id=999, user_id=2)
        
        self.assertFalse(success)
        self.assertIn("not found", message)
        self.session.add.assert_not_called()
        self.session.commit.assert_not_called()
        self.mock_event_producer_instance.send_like_event.assert_not_called()

    def test_like_post_error(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.user_id = 1
        mock_post.is_private = False
        
        query_post = MagicMock()
        filter_post = MagicMock()
        query_post.filter.return_value = filter_post
        filter_post.first.return_value = mock_post
        
        query_like = MagicMock()
        filter_like1 = MagicMock()
        filter_like2 = MagicMock()
        query_like.filter.return_value = filter_like1
        filter_like1.filter.return_value = filter_like2
        filter_like2.first.return_value = None
        
        def query_side_effect(model):
            if model == Post:
                return query_post
            elif model == PostLike:
                return query_like
            return MagicMock()
            
        self.session.query.side_effect = query_side_effect
        
        self.session.commit.side_effect = Exception("Database error")
        
        success, message = self.posts_service.like_post(post_id=1, user_id=2)
        
        self.assertFalse(success)
        self.assertIn("Database error", message)

    def test_create_comment(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.user_id = 1
        mock_post.is_private = False
        
        query = MagicMock()
        filter_result = MagicMock()
        query.filter.return_value = filter_result
        filter_result.first.return_value = mock_post
        
        self.session.query.return_value = query
        
        now = datetime.utcnow()
        expected_result = {
            'id': 1,
            'post_id': 1,
            'user_id': 2,
            'content': 'Test comment',
            'created_at': now.isoformat()
        }
        
        mock_comment = MagicMock(spec=Comment)
        mock_comment.id = 1
        mock_comment.post_id = 1
        mock_comment.user_id = 2
        mock_comment.content = 'Test comment'
        mock_comment.created_at = now
        mock_comment.to_dict.return_value = expected_result
        
        with patch('posts_service.Comment', return_value=mock_comment):
            result, error = self.posts_service.create_comment(
                post_id=1, 
                user_id=2, 
                content='Test comment'
            )
            
            self.assertEqual(result, expected_result)
            self.assertIsNone(error)
            self.session.add.assert_called_once()
            self.session.commit.assert_called_once()
            self.mock_event_producer_instance.send_comment_event.assert_called_once_with(
                user_id=2, post_id=1, comment_id=1
            )

    def test_create_comment_on_private_post_denied(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.user_id = 1
        mock_post.is_private = True
        
        query = MagicMock()
        filter_result = MagicMock()
        query.filter.return_value = filter_result
        filter_result.first.return_value = mock_post
        
        self.session.query.return_value = query
        
        result, error = self.posts_service.create_comment(
            post_id=1, 
            user_id=2, 
            content='Test comment'
        )
        
        self.assertIsNone(result)
        self.assertIn("Access denied", error)
        self.session.add.assert_not_called()
        self.session.commit.assert_not_called()
        self.mock_event_producer_instance.send_comment_event.assert_not_called()

    def test_create_comment_post_not_found(self):
        query = MagicMock()
        filter_result = MagicMock()
        query.filter.return_value = filter_result
        filter_result.first.return_value = None
        
        self.session.query.return_value = query
        
        result, error = self.posts_service.create_comment(
            post_id=999, 
            user_id=2, 
            content='Test comment'
        )
        
        self.assertIsNone(result)
        self.assertIn("not found", error)
        self.session.add.assert_not_called()
        self.session.commit.assert_not_called()
        self.mock_event_producer_instance.send_comment_event.assert_not_called()

    def test_create_comment_error(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        mock_post.user_id = 1
        mock_post.is_private = False
        
        query = MagicMock()
        filter_result = MagicMock()
        query.filter.return_value = filter_result
        filter_result.first.return_value = mock_post
        
        self.session.query.return_value = query
        
        self.session.commit.side_effect = Exception("Database error")
        
        result, error = self.posts_service.create_comment(
            post_id=1, 
            user_id=2, 
            content='Test comment'
        )
        
        self.assertIsNone(result)
        self.assertIn("Database error", error)
        self.session.add.assert_called_once()
        self.session.rollback.assert_called_once()
        self.mock_event_producer_instance.send_comment_event.assert_not_called()

    def test_list_comments(self):
        mock_post = MagicMock(spec=Post)
        mock_post.id = 1
        
        query_post = MagicMock()
        filter_post = MagicMock()
        query_post.filter.return_value = filter_post
        filter_post.first.return_value = mock_post
        
        now = datetime.utcnow()
        
        mock_comment1 = MagicMock(spec=Comment)
        mock_comment1.id = 1
        mock_comment1.post_id = 1
        mock_comment1.user_id = 2
        mock_comment1.content = 'First comment'
        mock_comment1.created_at = now
        mock_comment1.to_dict.return_value = {
            'id': 1,
            'post_id': 1,
            'user_id': 2,
            'content': 'First comment',
            'created_at': now.isoformat()
        }
        
        mock_comment2 = MagicMock(spec=Comment)
        mock_comment2.id = 2
        mock_comment2.post_id = 1
        mock_comment2.user_id = 3
        mock_comment2.content = 'Second comment'
        mock_comment2.created_at = now
        mock_comment2.to_dict.return_value = {
            'id': 2,
            'post_id': 1,
            'user_id': 3,
            'content': 'Second comment',
            'created_at': now.isoformat()
        }
        
        query_comments = MagicMock()
        filter_comments = MagicMock()
        count_result = MagicMock()
        order_by_result = MagicMock()
        offset_result = MagicMock()
        limit_result = MagicMock()
        
        query_comments.filter.return_value = filter_comments
        filter_comments.count.return_value = 2
        filter_comments.order_by.return_value = order_by_result
        order_by_result.offset.return_value = offset_result
        offset_result.limit.return_value = limit_result
        limit_result.all.return_value = [mock_comment1, mock_comment2]
        
        def query_side_effect(model):
            if model == Post:
                return query_post
            elif model == Comment:
                return query_comments
            return MagicMock()
            
        self.session.query.side_effect = query_side_effect
        
        result, error = self.posts_service.list_comments(post_id=1, page=1, per_page=10)
        
        self.assertIsNotNone(result)
        self.assertIsNone(error)
        self.assertEqual(len(result['comments']), 2)
        self.assertEqual(result['total_count'], 2)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['total_pages'], 1)
        
        self.assertEqual(result['comments'][0]['id'], 1)
        self.assertEqual(result['comments'][0]['content'], 'First comment')
        self.assertEqual(result['comments'][1]['id'], 2)
        self.assertEqual(result['comments'][1]['content'], 'Second comment')

    def test_list_comments_post_not_found(self):
        query = MagicMock()
        filter_result = MagicMock()
        query.filter.return_value = filter_result
        filter_result.first.return_value = None
        
        self.session.query.return_value = query
        
        result, error = self.posts_service.list_comments(post_id=999, page=1, per_page=10)
        
        self.assertIsNone(result)
        self.assertIn("not found", error)


if __name__ == '__main__':
    unittest.main()