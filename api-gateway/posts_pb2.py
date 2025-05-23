# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: posts.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'posts.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0bposts.proto\x12\x05posts\"j\n\x11\x43reatePostRequest\x12\r\n\x05title\x18\x01 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x02 \x01(\t\x12\x0f\n\x07user_id\x18\x03 \x01(\x05\x12\x12\n\nis_private\x18\x04 \x01(\x08\x12\x0c\n\x04tags\x18\x05 \x03(\t\"2\n\x0eGetPostRequest\x12\x0f\n\x07post_id\x18\x01 \x01(\x05\x12\x0f\n\x07user_id\x18\x02 \x01(\x05\"{\n\x11UpdatePostRequest\x12\x0f\n\x07post_id\x18\x01 \x01(\x05\x12\x0f\n\x07user_id\x18\x02 \x01(\x05\x12\r\n\x05title\x18\x03 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x04 \x01(\t\x12\x12\n\nis_private\x18\x05 \x01(\x08\x12\x0c\n\x04tags\x18\x06 \x03(\t\"5\n\x11\x44\x65letePostRequest\x12\x0f\n\x07post_id\x18\x01 \x01(\x05\x12\x0f\n\x07user_id\x18\x02 \x01(\x05\"6\n\x12\x44\x65letePostResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"P\n\x10ListPostsRequest\x12\x0c\n\x04page\x18\x01 \x01(\x05\x12\x10\n\x08per_page\x18\x02 \x01(\x05\x12\x0f\n\x07user_id\x18\x03 \x01(\x05\x12\x0b\n\x03tag\x18\x04 \x01(\t\"g\n\x11ListPostsResponse\x12\x1a\n\x05posts\x18\x01 \x03(\x0b\x32\x0b.posts.Post\x12\x13\n\x0btotal_count\x18\x02 \x01(\x05\x12\x0c\n\x04page\x18\x03 \x01(\x05\x12\x13\n\x0btotal_pages\x18\x04 \x01(\x05\"\x91\x01\n\x04Post\x12\n\n\x02id\x18\x01 \x01(\x05\x12\r\n\x05title\x18\x02 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x03 \x01(\t\x12\x0f\n\x07user_id\x18\x04 \x01(\x05\x12\x12\n\nis_private\x18\x05 \x01(\x08\x12\x0c\n\x04tags\x18\x06 \x03(\t\x12\x12\n\ncreated_at\x18\x07 \x01(\t\x12\x12\n\nupdated_at\x18\x08 \x01(\t\"8\n\x0cPostResponse\x12\x19\n\x04post\x18\x01 \x01(\x0b\x32\x0b.posts.Post\x12\r\n\x05\x65rror\x18\x02 \x01(\t\"3\n\x0fViewPostRequest\x12\x0f\n\x07post_id\x18\x01 \x01(\x05\x12\x0f\n\x07user_id\x18\x02 \x01(\x05\"4\n\x10ViewPostResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"3\n\x0fLikePostRequest\x12\x0f\n\x07post_id\x18\x01 \x01(\x05\x12\x0f\n\x07user_id\x18\x02 \x01(\x05\"4\n\x10LikePostResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"I\n\x14\x43reateCommentRequest\x12\x0f\n\x07post_id\x18\x01 \x01(\x05\x12\x0f\n\x07user_id\x18\x02 \x01(\x05\x12\x0f\n\x07\x63ontent\x18\x03 \x01(\t\"A\n\x0f\x43ommentResponse\x12\x1f\n\x07\x63omment\x18\x01 \x01(\x0b\x32\x0e.posts.Comment\x12\r\n\x05\x65rror\x18\x02 \x01(\t\"\\\n\x07\x43omment\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x0f\n\x07post_id\x18\x02 \x01(\x05\x12\x0f\n\x07user_id\x18\x03 \x01(\x05\x12\x0f\n\x07\x63ontent\x18\x04 \x01(\t\x12\x12\n\ncreated_at\x18\x05 \x01(\t\"F\n\x13ListCommentsRequest\x12\x0f\n\x07post_id\x18\x01 \x01(\x05\x12\x0c\n\x04page\x18\x02 \x01(\x05\x12\x10\n\x08per_page\x18\x03 \x01(\x05\"p\n\x14ListCommentsResponse\x12 \n\x08\x63omments\x18\x01 \x03(\x0b\x32\x0e.posts.Comment\x12\x13\n\x0btotal_count\x18\x02 \x01(\x05\x12\x0c\n\x04page\x18\x03 \x01(\x05\x12\x13\n\x0btotal_pages\x18\x04 \x01(\x05\x32\xca\x04\n\x0bPostService\x12;\n\nCreatePost\x12\x18.posts.CreatePostRequest\x1a\x13.posts.PostResponse\x12\x35\n\x07GetPost\x12\x15.posts.GetPostRequest\x1a\x13.posts.PostResponse\x12;\n\nUpdatePost\x12\x18.posts.UpdatePostRequest\x1a\x13.posts.PostResponse\x12\x41\n\nDeletePost\x12\x18.posts.DeletePostRequest\x1a\x19.posts.DeletePostResponse\x12>\n\tListPosts\x12\x17.posts.ListPostsRequest\x1a\x18.posts.ListPostsResponse\x12;\n\x08ViewPost\x12\x16.posts.ViewPostRequest\x1a\x17.posts.ViewPostResponse\x12;\n\x08LikePost\x12\x16.posts.LikePostRequest\x1a\x17.posts.LikePostResponse\x12\x44\n\rCreateComment\x12\x1b.posts.CreateCommentRequest\x1a\x16.posts.CommentResponse\x12G\n\x0cListComments\x12\x1a.posts.ListCommentsRequest\x1a\x1b.posts.ListCommentsResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'posts_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_CREATEPOSTREQUEST']._serialized_start=22
  _globals['_CREATEPOSTREQUEST']._serialized_end=128
  _globals['_GETPOSTREQUEST']._serialized_start=130
  _globals['_GETPOSTREQUEST']._serialized_end=180
  _globals['_UPDATEPOSTREQUEST']._serialized_start=182
  _globals['_UPDATEPOSTREQUEST']._serialized_end=305
  _globals['_DELETEPOSTREQUEST']._serialized_start=307
  _globals['_DELETEPOSTREQUEST']._serialized_end=360
  _globals['_DELETEPOSTRESPONSE']._serialized_start=362
  _globals['_DELETEPOSTRESPONSE']._serialized_end=416
  _globals['_LISTPOSTSREQUEST']._serialized_start=418
  _globals['_LISTPOSTSREQUEST']._serialized_end=498
  _globals['_LISTPOSTSRESPONSE']._serialized_start=500
  _globals['_LISTPOSTSRESPONSE']._serialized_end=603
  _globals['_POST']._serialized_start=606
  _globals['_POST']._serialized_end=751
  _globals['_POSTRESPONSE']._serialized_start=753
  _globals['_POSTRESPONSE']._serialized_end=809
  _globals['_VIEWPOSTREQUEST']._serialized_start=811
  _globals['_VIEWPOSTREQUEST']._serialized_end=862
  _globals['_VIEWPOSTRESPONSE']._serialized_start=864
  _globals['_VIEWPOSTRESPONSE']._serialized_end=916
  _globals['_LIKEPOSTREQUEST']._serialized_start=918
  _globals['_LIKEPOSTREQUEST']._serialized_end=969
  _globals['_LIKEPOSTRESPONSE']._serialized_start=971
  _globals['_LIKEPOSTRESPONSE']._serialized_end=1023
  _globals['_CREATECOMMENTREQUEST']._serialized_start=1025
  _globals['_CREATECOMMENTREQUEST']._serialized_end=1098
  _globals['_COMMENTRESPONSE']._serialized_start=1100
  _globals['_COMMENTRESPONSE']._serialized_end=1165
  _globals['_COMMENT']._serialized_start=1167
  _globals['_COMMENT']._serialized_end=1259
  _globals['_LISTCOMMENTSREQUEST']._serialized_start=1261
  _globals['_LISTCOMMENTSREQUEST']._serialized_end=1331
  _globals['_LISTCOMMENTSRESPONSE']._serialized_start=1333
  _globals['_LISTCOMMENTSRESPONSE']._serialized_end=1445
  _globals['_POSTSERVICE']._serialized_start=1448
  _globals['_POSTSERVICE']._serialized_end=2034
# @@protoc_insertion_point(module_scope)
