from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from src.linkedin_extractor.services.apiManager import LinkedInAPIManager
from typing import Any

app = FastAPI()
api_manager = LinkedInAPIManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to specific domains like ["http://localhost:8501"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "LinkedIn Extractor API is live!"}

@app.get("/extract-profile")
def extract(username: str):
    result = api_manager.fetch_profile_data_by_username(username)
    return result

@app.get("/extract-posts")
def extract_posts(username: str = Query(..., description="LinkedIn username")):
    posts = api_manager.fetch_recent_posts_by_username(username)
    return posts

@app.get("/extract-comments")
def extract_comments(username: str = Query(..., description="LinkedIn username")):
    comments = api_manager.fetch_profile_comments_by_username(username)
    return comments

@app.get("/extract-likes")
def extract_likes(username: str = Query(..., description="LinkedIn username")):
    likes = api_manager.fetch_profile_likes_by_username(username)
    return likes

@app.get("/extract-post-comments")
def extract_post_comments(urn: str = Query(...), count: int = Query(10)):
    comments = api_manager.fetch_comments_by_post_urn(urn, count)
    return comments
    
@app.get("/extract-all")
def extract_all(
    username: str = Query(..., description="LinkedIn username"),
    extract_comments: str = Query("no", description="yes or no"),
    count: int = Query(10, description="Number of comments per post if extract_comments is yes")
) -> dict[str, Any]:
    api_manager.api_calls = 0
    profile = api_manager.fetch_profile_data_by_username(username)
    print(profile)
    posts_result =  api_manager.fetch_recent_posts_by_username(username)
    comments =  api_manager.fetch_profile_comments_by_username(username)
    likes =  api_manager.fetch_profile_likes_by_username(username)

    posts = posts_result.posts
    reposts = posts_result.reposts

    posts_output = []

    if extract_comments.lower() == "yes":
        for post in posts:
            post_dict = post.dict()
            post_dict["comments"] =  api_manager.fetch_comments_by_post_urn(post.urn, count)
            posts_output.append(post_dict)
    else:
        posts_output = [post.dict() for post in posts]
        

    return {
        "profile": profile.dict(),
        "posts": posts_output,
        "reposts": reposts,
        "commented_posts": comments,
        "reacted_posts": likes,
        "credits_used": api_manager.get_credit_usage()
    }
    
@app.get("/extract-all-threading")
def extract_all(username: str = Query(..., description="LinkedIn username")):
    result = {}
    with ThreadPoolExecutor() as executor:
        futures = {
            "profile": executor.submit(api_manager.fetch_profile_data_by_username, username),
            "posts": executor.submit(api_manager.fetch_recent_posts_by_username, username),
            "comments": executor.submit(api_manager.fetch_profile_comments_by_username, username),
            "likes": executor.submit(api_manager.fetch_profile_likes_by_username, username)
        }

        for key, future in futures.items():
            try:
                result[key] = future.result()
            except Exception as e:
                result[key] = {"error": str(e)}

    return result

