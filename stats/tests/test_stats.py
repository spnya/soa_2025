import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
import sys
import os

# Add the parent directory to the path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_clickhouse_client():
    """Fixture для мока ClickHouse клиента"""
    with patch('consumer.Client') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def consumer(mock_clickhouse_client):
    """Fixture для создания consumer с мокнутым ClickHouse"""
    from consumer import StatisticsEventConsumer
    return StatisticsEventConsumer(
        bootstrap_servers='test:9092',
        clickhouse_host='test_host',
        clickhouse_port=9000
    )


@pytest.fixture
def mock_grpc_modules():
    """Fixture для мокания gRPC модулей"""
    with patch.dict('sys.modules', {
        'statistics_pb2': Mock(),
        'statistics_pb2_grpc': Mock()
    }):
        # Настройка мок объектов
        sys.modules['statistics_pb2'].PostStats = Mock()
        sys.modules['statistics_pb2'].GetPostStatsResponse = Mock()
        sys.modules['statistics_pb2'].DayStats = Mock()
        sys.modules['statistics_pb2'].GetPostDynamicsResponse = Mock()
        sys.modules['statistics_pb2'].GetTopPostsRequest = Mock()
        sys.modules['statistics_pb2'].GetTopPostsResponse = Mock()
        sys.modules['statistics_pb2'].GetTopUsersRequest = Mock()
        sys.modules['statistics_pb2'].GetTopUsersResponse = Mock()
        sys.modules['statistics_pb2'].UserStats = Mock()
        yield


@pytest.fixture
def statistics_service(mock_grpc_modules):
    """Fixture для создания gRPC сервиса с мокнутым ClickHouse"""
    with patch('statistics_server.Client') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        from statistics_server import StatisticsService
        service = StatisticsService(
            clickhouse_host='test_host',
            clickhouse_port=9000
        )
        service.clickhouse_client = mock_instance
        yield service, mock_instance


class TestConsumerEventProcessing:
    """Тесты обработки событий в consumer"""
    

    def test_process_post_like_event(self, consumer, mock_clickhouse_client):
        """Тест обработки события лайка поста"""
        event_data = {
            'event_type': 'post_like',
            'user_id': 1,
            'post_id': 6,
            'timestamp': '2025-05-25T18:31:09.578311'
        }
        
        result = consumer._process_event(event_data)
        
        assert result is True
        call_args = mock_clickhouse_client.execute.call_args
        insert_data = call_args[0][1][0]
        
        assert insert_data['event_type'] == 'post_like'
        assert insert_data['user_id'] == 1
        assert insert_data['post_id'] == 6
    
    def test_process_post_comment_event(self, consumer, mock_clickhouse_client):
        """Тест обработки события комментария"""
        event_data = {
            'event_type': 'post_comment',
            'user_id': 1,
            'post_id': 6,
            'comment_id': 12,
            'timestamp': '2025-05-25T18:31:26.689909'
        }
        
        result = consumer._process_event(event_data)
        
        assert result is True
        call_args = mock_clickhouse_client.execute.call_args
        insert_data = call_args[0][1][0]
        
        assert insert_data['event_type'] == 'post_comment'
        assert insert_data['comment_id'] == 12
    
    def test_process_event_invalid_timestamp(self, consumer, mock_clickhouse_client):
        """Тест обработки события с некорректным timestamp"""
        event_data = {
            'event_type': 'post_view',
            'user_id': 1,
            'post_id': 123,
            'timestamp': 'invalid-timestamp'
        }
        
        result = consumer._process_event(event_data)
        
        assert result is False
    
    def test_process_event_clickhouse_error(self, consumer, mock_clickhouse_client):
        """Тест обработки ошибки ClickHouse"""
        event_data = {
            'event_type': 'post_view',
            'user_id': 1,
            'post_id': 123,
            'timestamp': '2025-05-25T18:31:14.469322'
        }
        
        mock_clickhouse_client.execute.side_effect = Exception("ClickHouse error")
        
        result = consumer._process_event(event_data)
        
        assert result is False
    
    @patch('consumer.KafkaConsumer')
    def test_init_consumer_success(self, mock_kafka_consumer, consumer):
        """Тест успешной инициализации Kafka consumer"""
        mock_consumer_instance = Mock()
        mock_kafka_consumer.return_value = mock_consumer_instance
        
        result = consumer._init_consumer()
        
        assert result is True
        assert consumer.consumer == mock_consumer_instance
        
        # Проверяем параметры инициализации
        mock_kafka_consumer.assert_called_once_with(
            'user_registrations',
            'post_likes', 
            'post_views',
            'post_comments',
            bootstrap_servers='test:9092',
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='statistics_consumer_group',
            value_deserializer=mock_kafka_consumer.call_args[1]['value_deserializer'],
            consumer_timeout_ms=1000,
            api_version=(0, 10)
        )

 
if __name__ == '__main__':
    pytest.main([__file__])