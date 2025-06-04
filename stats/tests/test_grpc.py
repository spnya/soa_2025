import pytest
from unittest.mock import MagicMock
import sys
import os

# Add the parent directory to the path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statistics_pb2 import (
    GetPostStatsRequest,
    GetPostDynamicsRequest,
    GetTopPostsRequest,
    GetPostStatsResponse,
    GetPostDynamicsResponse,
    GetTopPostsResponse,
    PostStats,
    DayStats
)
from statistics_pb2_grpc import StatisticsServiceServicer
from statistics_server import StatisticsService


@pytest.fixture
def mock_clickhouse_client():
    return MagicMock()


@pytest.fixture
def service(mock_clickhouse_client):
    service = StatisticsService.__new__(StatisticsService)
    service.clickhouse_client = mock_clickhouse_client
    return service


def test_get_post_stats(service, mock_clickhouse_client):
    mock_clickhouse_client.execute.return_value = [(42, 100, 20, 5)]

    request = GetPostStatsRequest(post_id=42)
    context = MagicMock()

    response = service.GetPostStats(request, context)

    assert isinstance(response, GetPostStatsResponse)
    assert response.stats.post_id == 42
    assert response.stats.views == 100
    assert response.stats.likes == 20
    assert response.stats.comments == 5


def test_get_post_views_dynamics(service, mock_clickhouse_client):
    mock_clickhouse_client.execute.return_value = [
        ('2024-01-01', 10),
        ('2024-01-02', 5)
    ]

    request = GetPostDynamicsRequest(post_id=42, start_date='2024-01-01', end_date='2024-01-02')
    context = MagicMock()

    response = service.GetPostViewsDynamics(request, context)

    assert isinstance(response, GetPostDynamicsResponse)
    assert len(response.dynamics) == 2
    assert response.dynamics[0].date == '2024-01-01'
    assert response.dynamics[0].count == 10


def test_get_top_posts(service, mock_clickhouse_client):
    mock_clickhouse_client.execute.return_value = [
        (101, 50, 20, 5),
        (102, 40, 10, 3)
    ]

    request = GetTopPostsRequest(metric=GetTopPostsRequest.VIEWS, limit=2)
    context = MagicMock()

    response = service.GetTopPosts(request, context)

    assert isinstance(response, GetTopPostsResponse)
    assert len(response.posts) == 2
    assert response.posts[0].post_id == 101
    assert response.posts[0].views == 50
    assert response.posts[0].likes == 20
    assert response.posts[0].comments == 5
