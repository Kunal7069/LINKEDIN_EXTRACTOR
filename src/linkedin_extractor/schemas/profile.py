# from pydantic import BaseModel, Field
# from typing import List, Optional

# # Input schema
# class ProfileRequest(BaseModel):
#     username: str = Field(..., example="kunal-jain-286020233")


# # Output schema
# class ProfileResponse(BaseModel):
#     headline: str | None
#     location: str | None
#     job_title: str | None
#     company_name: str | None


# class Post(BaseModel):
#     postedDate: str
#     text: Optional[str] = None
#     postUrl: Optional[str] = None
#     totalReactionCount: Optional[int] = None
#     commentsCount: Optional[int] = None
#     urn: Optional[str] = None

# class PostListResponse(BaseModel):
#     posts: List[Post]
#     reposts: List[Post]

from pydantic import BaseModel, Field, RootModel
from typing import Optional, List, TypedDict


# Input Schemas
class UsernameInput(BaseModel):
    username: str


# Output Schemas

class ProfileOutput(BaseModel):
    headline: Optional[str]
    location: Optional[str]
    job_title: Optional[str]
    company_name: Optional[str]


class PostData(BaseModel):
    postedDate: str
    totalReactionCount: Optional[int]
    commentsCount: Optional[int]
    urn: Optional[str]
    text: Optional[str]
    original_text: Optional[str] = None


class PostOutput(BaseModel):
    posts: List[PostData]
    reposts: List[PostData]


class CommentData(BaseModel):
    highlightedComments: Optional[str]
    text: Optional[str]
    postedDate: Optional[str]
    commentedDate: Optional[str]
    postUrl: Optional[str]


class CommentsOutput(RootModel[List[CommentData]]):
    pass


class LikeData(BaseModel):
    text: Optional[str]
    action: Optional[str]
    postedDate: Optional[str]
    totalReactionCount: Optional[int]
    commentsCount: Optional[int]


class LikesOutput(RootModel[List[LikeData]]):
    pass