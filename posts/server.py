import grpc
from concurrent import futures
import time
import os
import posts_pb2
import posts_pb2_grpc
from posts_service import PostsService
from models import init_db
from config import Config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class PostServicer(posts_pb2_grpc.PostServiceServicer):
    def __init__(self, posts_service):
        self.posts_service = posts_service

    def CreatePost(self, request, context):
        post_data, error = self.posts_service.create_post(
            title=request.title,
            description=request.description,
            user_id=request.user_id,
            is_private=request.is_private,
            tags=list(request.tags)
        )
        
        if error:
            return posts_pb2.PostResponse(error=error)
            
        post = posts_pb2.Post(
            id=post_data['id'],
            title=post_data['title'],
            description=post_data['description'],
            user_id=post_data['user_id'],
            is_private=post_data['is_private'],
            tags=post_data['tags'],
            created_at=post_data['created_at'],
            updated_at=post_data['updated_at']
        )
        
        return posts_pb2.PostResponse(post=post)

    def GetPost(self, request, context):
        post_data, error = self.posts_service.get_post(
            post_id=request.post_id,
            user_id=request.user_id
        )
        
        if error:
            return posts_pb2.PostResponse(error=error)
            
        post = posts_pb2.Post(
            id=post_data['id'],
            title=post_data['title'],
            description=post_data['description'],
            user_id=post_data['user_id'],
            is_private=post_data['is_private'],
            tags=post_data['tags'],
            created_at=post_data['created_at'],
            updated_at=post_data['updated_at']
        )
        
        return posts_pb2.PostResponse(post=post)

    def UpdatePost(self, request, context):
        post_data, error = self.posts_service.update_post(
            post_id=request.post_id,
            user_id=request.user_id,
            title=request.title,
            description=request.description,
            is_private=request.is_private,
            tags=list(request.tags)
        )
        
        if error:
            return posts_pb2.PostResponse(error=error)
            
        post = posts_pb2.Post(
            id=post_data['id'],
            title=post_data['title'],
            description=post_data['description'],
            user_id=post_data['user_id'],
            is_private=post_data['is_private'],
            tags=post_data['tags'],
            created_at=post_data['created_at'],
            updated_at=post_data['updated_at']
        )
        
        return posts_pb2.PostResponse(post=post)

    def DeletePost(self, request, context):
        success, message = self.posts_service.delete_post(
            post_id=request.post_id,
            user_id=request.user_id
        )
        
        return posts_pb2.DeletePostResponse(
            success=success,
            message=message
        )

    def ListPosts(self, request, context):
        result, error = self.posts_service.list_posts(
            page=request.page,
            per_page=request.per_page,
            user_id=request.user_id,
            tag=request.tag if request.tag else None
        )
        
        if error:
            return posts_pb2.ListPostsResponse()
            
        posts_proto = []
        for post_data in result['posts']:
            post = posts_pb2.Post(
                id=post_data['id'],
                title=post_data['title'],
                description=post_data['description'],
                user_id=post_data['user_id'],
                is_private=post_data['is_private'],
                tags=post_data['tags'],
                created_at=post_data['created_at'],
                updated_at=post_data['updated_at']
            )
            posts_proto.append(post)
            
        return posts_pb2.ListPostsResponse(
            posts=posts_proto,
            total_count=result['total_count'],
            page=result['page'],
            total_pages=result['total_pages']
        )
    
    # New methods that implement the gRPC service definitions
    def ViewPost(self, request, context):
        success, message = self.posts_service.view_post(
            post_id=request.post_id,
            user_id=request.user_id
        )
        
        return posts_pb2.ViewPostResponse(
            success=success,
            message=message
        )
    
    def LikePost(self, request, context):
        success, message = self.posts_service.like_post(
            post_id=request.post_id,
            user_id=request.user_id
        )
        
        return posts_pb2.LikePostResponse(
            success=success,
            message=message
        )
    
    def CreateComment(self, request, context):
        comment_data, error = self.posts_service.create_comment(
            post_id=request.post_id,
            user_id=request.user_id,
            content=request.content
        )
        
        if error:
            return posts_pb2.CommentResponse(error=error)
            
        comment = posts_pb2.Comment(
            id=comment_data['id'],
            post_id=comment_data['post_id'],
            user_id=comment_data['user_id'],
            content=comment_data['content'],
            created_at=comment_data['created_at']
        )
        
        return posts_pb2.CommentResponse(comment=comment)
    
    def ListComments(self, request, context):
        result, error = self.posts_service.list_comments(
            post_id=request.post_id,
            page=request.page,
            per_page=request.per_page
        )
        
        if error:
            return posts_pb2.ListCommentsResponse()
            
        comments_proto = []
        for comment_data in result['comments']:
            comment = posts_pb2.Comment(
                id=comment_data['id'],
                post_id=comment_data['post_id'],
                user_id=comment_data['user_id'],
                content=comment_data['content'],
                created_at=comment_data['created_at']
            )
            comments_proto.append(comment)
            
        return posts_pb2.ListCommentsResponse(
            comments=comments_proto,
            total_count=result['total_count'],
            page=result['page'],
            total_pages=result['total_pages']
        )


def serve():
    db_session = init_db(Config.DATABASE_URL)
    posts_service = PostsService(db_session)
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    posts_pb2_grpc.add_PostServiceServicer_to_server(
        PostServicer(posts_service), server
    )
    
    server.add_insecure_port(f'[::]:{Config.GRPC_PORT}')
    server.start()
    
    logging.info(f"Posts gRPC server started on port {Config.GRPC_PORT}")
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
        logging.info("Posts gRPC server stopped")


if __name__ == '__main__':
    serve()