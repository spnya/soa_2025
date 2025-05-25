import grpc
from concurrent import futures
import statistics_pb2
import statistics_pb2_grpc
from clickhouse_driver import Client
import logging
from datetime import datetime, date
from typing import List, Dict, Any
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatisticsService(statistics_pb2_grpc.StatisticsServiceServicer):
    def __init__(self, clickhouse_host: str = 'localhost', clickhouse_port: int = 9000):
        """
        Initialize the statistics service
        
        Args:
            clickhouse_host: ClickHouse host
            clickhouse_port: ClickHouse port
        """
        try:
            self.clickhouse_client = Client(
                host=clickhouse_host,
                port=clickhouse_port,
                database='statistics'
            )
            logger.info(f"Connected to ClickHouse at {clickhouse_host}:{clickhouse_port}")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {str(e)}")
            raise
    
    def GetPostStats(self, request, context):
        """Получение общей статистики по посту"""
        try:
            post_id = request.post_id
            
            query = """
                SELECT 
                    post_id,
                    sum(views) as total_views,
                    sum(likes) as total_likes,
                    sum(comments) as total_comments
                FROM statistics.post_stats
                WHERE post_id = %(post_id)s
                GROUP BY post_id
            """
            
            result = self.clickhouse_client.execute(query, {'post_id': post_id})
            
            if not result:
                # Если данных нет в агрегированной таблице, проверим в основной
                query_raw = """
                    SELECT 
                        post_id,
                        countIf(event_type = 'post_view') as views,
                        countIf(event_type = 'post_like') as likes,
                        countIf(event_type = 'post_comment') as comments
                    FROM statistics.events
                    WHERE post_id = %(post_id)s
                    GROUP BY post_id
                """
                
                result = self.clickhouse_client.execute(query_raw, {'post_id': post_id})
            
            if result:
                row = result[0]
                stats = statistics_pb2.PostStats(
                    post_id=row[0],
                    views=row[1],
                    likes=row[2],
                    comments=row[3]
                )
            else:
                # Пост не найден или нет статистики
                stats = statistics_pb2.PostStats(
                    post_id=post_id,
                    views=0,
                    likes=0,
                    comments=0
                )
            
            return statistics_pb2.GetPostStatsResponse(stats=stats)
            
        except Exception as e:
            logger.error(f"Error getting post stats for post {request.post_id}: {str(e)}")
            return statistics_pb2.GetPostStatsResponse(
                error=f"Internal server error: {str(e)}"
            )
    
    def GetPostViewsDynamics(self, request, context):
        """Получение динамики просмотров по посту"""
        return self._get_post_dynamics(request, 'post_view')
    
    def GetPostLikesDynamics(self, request, context):
        """Получение динамики лайков по посту"""
        return self._get_post_dynamics(request, 'post_like')
    
    def GetPostCommentsDynamics(self, request, context):
        """Получение динамики комментариев по посту"""
        return self._get_post_dynamics(request, 'post_comment')
    
    def _get_post_dynamics(self, request, event_type: str):
        """Вспомогательный метод для получения динамики по типу события"""
        try:
            post_id = request.post_id
            start_date = request.start_date or '2020-01-01'
            end_date = request.end_date or datetime.now().strftime('%Y-%m-%d')
            
            # Сначала попробуем получить из агрегированной таблицы
            if event_type == 'post_view':
                column = 'views'
            elif event_type == 'post_like':
                column = 'likes'
            else:  # post_comment
                column = 'comments'
            
            query = f"""
                SELECT 
                    date,
                    sum({column}) as count
                FROM statistics.daily_post_stats
                WHERE post_id = %(post_id)s
                  AND date >= %(start_date)s
                  AND date <= %(end_date)s
                GROUP BY date
                ORDER BY date
            """
            
            result = self.clickhouse_client.execute(query, {
                'post_id': post_id,
                'start_date': start_date,
                'end_date': end_date
            })
            
            if not result:
                # Если данных нет в агрегированной таблице, получаем из основной
                query_raw = f"""
                    SELECT 
                        date,
                        count(*) as count
                    FROM statistics.events
                    WHERE post_id = %(post_id)s
                      AND event_type = %(event_type)s
                      AND date >= %(start_date)s
                      AND date <= %(end_date)s
                    GROUP BY date
                    ORDER BY date
                """
                
                result = self.clickhouse_client.execute(query_raw, {
                    'post_id': post_id,
                    'event_type': event_type,
                    'start_date': start_date,
                    'end_date': end_date
                })
            
            dynamics = []
            for row in result:
                day_stats = statistics_pb2.DayStats(
                    date=str(row[0]),
                    count=row[1]
                )
                dynamics.append(day_stats)
            
            return statistics_pb2.GetPostDynamicsResponse(dynamics=dynamics)
            
        except Exception as e:
            logger.error(f"Error getting post dynamics for post {request.post_id}: {str(e)}")
            return statistics_pb2.GetPostDynamicsResponse(
                error=f"Internal server error: {str(e)}"
            )
    
    def GetTopPosts(self, request, context):
        """Получение топ постов"""
        try:
            metric_map = {
                statistics_pb2.GetTopPostsRequest.VIEWS: 'views',
                statistics_pb2.GetTopPostsRequest.LIKES: 'likes',
                statistics_pb2.GetTopPostsRequest.COMMENTS: 'comments'
            }
            
            metric = metric_map.get(request.metric, 'views')
            limit = request.limit or 10
            
            query = f"""
                SELECT 
                    post_id,
                    sum(views) as total_views,
                    sum(likes) as total_likes, 
                    sum(comments) as total_comments
                FROM statistics.post_stats
                GROUP BY post_id
                ORDER BY sum({metric}) DESC
                LIMIT %(limit)s
            """
            
            result = self.clickhouse_client.execute(query, {'limit': limit})
            
            if not result:
                # Если данных нет в агрегированной таблице, получаем из основной
                query_raw = f"""
                    SELECT 
                        post_id,
                        countIf(event_type = 'post_view') as views,
                        countIf(event_type = 'post_like') as likes,
                        countIf(event_type = 'post_comment') as comments
                    FROM statistics.events
                    WHERE post_id IS NOT NULL
                    GROUP BY post_id
                    ORDER BY countIf(event_type = %(event_type)s) DESC
                    LIMIT %(limit)s
                """
                
                event_type_map = {
                    'views': 'post_view',
                    'likes': 'post_like',
                    'comments': 'post_comment'
                }
                
                result = self.clickhouse_client.execute(query_raw, {
                    'event_type': event_type_map[metric],
                    'limit': limit
                })
            
            posts = []
            for row in result:
                post_stats = statistics_pb2.PostStats(
                    post_id=row[0],
                    views=row[1],
                    likes=row[2],
                    comments=row[3]
                )
                posts.append(post_stats)
            
            return statistics_pb2.GetTopPostsResponse(posts=posts)
            
        except Exception as e:
            logger.error(f"Error getting top posts: {str(e)}")
            return statistics_pb2.GetTopPostsResponse(
                error=f"Internal server error: {str(e)}"
            )
    
    def GetTopUsers(self, request, context):
        """Получение топ пользователей"""
        try:
            metric_map = {
                statistics_pb2.GetTopUsersRequest.VIEWS: 'views',
                statistics_pb2.GetTopUsersRequest.LIKES: 'likes',
                statistics_pb2.GetTopUsersRequest.COMMENTS: 'comments'
            }
            
            metric = metric_map.get(request.metric, 'views')
            limit = request.limit or 10
            
            query = f"""
                SELECT 
                    user_id,
                    sum(views) as total_views,
                    sum(likes) as total_likes,
                    sum(comments) as total_comments
                FROM statistics.user_stats
                GROUP BY user_id
                ORDER BY sum({metric}) DESC
                LIMIT %(limit)s
            """
            
            result = self.clickhouse_client.execute(query, {'limit': limit})
            
            if not result:
                # Если данных нет в агрегированной таблице, получаем из основной
                query_raw = f"""
                    SELECT 
                        user_id,
                        countIf(event_type = 'post_view') as views,
                        countIf(event_type = 'post_like') as likes,
                        countIf(event_type = 'post_comment') as comments
                    FROM statistics.events
                    GROUP BY user_id
                    ORDER BY countIf(event_type = %(event_type)s) DESC
                    LIMIT %(limit)s
                """
                
                event_type_map = {
                    'views': 'post_view',
                    'likes': 'post_like',
                    'comments': 'post_comment'
                }
                
                result = self.clickhouse_client.execute(query_raw, {
                    'event_type': event_type_map[metric],
                    'limit': limit
                })
            
            users = []
            for row in result:
                user_stats = statistics_pb2.UserStats(
                    user_id=row[0],
                    views=row[1],
                    likes=row[2],
                    comments=row[3]
                )
                users.append(user_stats)
            
            return statistics_pb2.GetTopUsersResponse(users=users)
            
        except Exception as e:
            logger.error(f"Error getting top users: {str(e)}")
            return statistics_pb2.GetTopUsersResponse(
                error=f"Internal server error: {str(e)}"
            )


def serve():
    """Запуск gRPC сервера"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    clickhouse_host = os.getenv('CLICKHOUSE_HOST', 'clickhouse')
    clickhouse_port = int(os.getenv('CLICKHOUSE_PORT', '9000'))
    
    statistics_service = StatisticsService(
        clickhouse_host=clickhouse_host,
        clickhouse_port=clickhouse_port
    )
    
    statistics_pb2_grpc.add_StatisticsServiceServicer_to_server(
        statistics_service, 
        server
    )
    
    grpc_port = os.getenv('GRPC_PORT', '50052')
    listen_addr = f'[::]:{grpc_port}'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting Statistics gRPC server on {listen_addr}")
    server.start()
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Server interrupted")
        server.stop(0)


if __name__ == '__main__':
    serve()