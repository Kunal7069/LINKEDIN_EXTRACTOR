import http.client
from datetime import datetime, timedelta
import json
from src.linkedin_extractor.config.config import settings
from src.linkedin_extractor.schemas.profile import (
    UsernameInput,
    ProfileOutput,
    PostOutput,
    PostData,
    CommentsOutput,
    LikesOutput
)

class LinkedInAPIManager:
    
    def __init__(self):
        self.headers = {
            'x-rapidapi-key': settings.RAPIDAPI_KEY,
            'x-rapidapi-host': settings.RAPIDAPI_HOST
        }
        self.api_calls = 0
        self.conn = http.client.HTTPSConnection(settings.RAPIDAPI_HOST)
        
    def get_credit_usage(self) -> int:
        return self.api_calls

    def _make_api_request(self, path: str):
        try:
            # Create a fresh connection every time
            self.api_calls += 1
            # conn = http.client.HTTPSConnection(settings.RAPIDAPI_HOST)
            self.conn.request("GET", path, headers=self.headers)
            res = self.conn.getresponse()
            data = res.read()
            self.conn.close()
            return json.loads(data.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"API request failed: {e}")

    def fetch_profile_data_by_username(self, username: str) -> ProfileOutput:
        validated_input = UsernameInput(username=username)
        path = f"/?username={validated_input.username}"
        decoded_data = self._make_api_request(path)
        output_data = {
            "headline": decoded_data.get("headline"),
            "location": decoded_data.get("geo", {}).get("full"),
            "job_title": None,
            "company_name": None,
        }
        
        position = decoded_data.get("position", [])
        first_position = position[0] if position else {}
        output_data["job_title"] = first_position.get("title")
        output_data["company_name"] = first_position.get("companyName")
        
        validated_output = ProfileOutput(**output_data)
        return validated_output

   
    
    def fetch_recent_posts_by_username(self, username: str) -> PostOutput:
        validated_input = UsernameInput(username=username)
        posts = []
        reposts = []
        start = 0
        pagination_token = None
        now = datetime.utcnow()
        twelve_months_ago = now - timedelta(days=365)  # fixed to 12 months, adjust if needed

        while True:
            query = f"/get-profile-posts?username={validated_input.username}&start={start}"
            if pagination_token:
                query += f"&paginationToken={pagination_token}"

            decoded_data = self._make_api_request(query)
            print(decoded_data)
            raw_posts = decoded_data.get("data", [])
            pagination_token = decoded_data.get("nextToken")

            if not raw_posts:
                break

            stop_fetching = False
            for post in raw_posts:
                posted_at_str = post.get("postedDate")
                if not posted_at_str:
                    continue

                try:
                    posted_at = datetime.strptime(posted_at_str[:19], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue

                if posted_at < twelve_months_ago:
                    stop_fetching = True
                    break

                is_repost = "reposted" in post
                original_text = None

                if is_repost:
                    reshared = post.get("resharedPost", {})
                    original_text = reshared.get("text") or post.get("text")

                base_data = {
                    "postedDate": posted_at_str,
                    "totalReactionCount": post.get("totalReactionCount"),
                    "commentsCount": post.get("commentsCount"),
                    "urn": post.get("urn"),
                    "text": post.get("text"),
                    "original_text": original_text
                }

                if is_repost:
                    reposts.append(PostData(**base_data))
                else:
                    posts.append(PostData(**base_data))

            if stop_fetching or not pagination_token:
                break

            start += 50

        output_data = {"posts": posts, "reposts": reposts}
        validated_output = PostOutput(**output_data)
        return validated_output

    def fetch_profile_comments_by_username(self, username: str) -> CommentsOutput:
        validated_input = UsernameInput(username=username)
        path = f"/get-profile-comments?username={validated_input.username}"
        decoded_data = self._make_api_request(path)
        raw_comments = decoded_data.get("data", [])

        output_data = [
            {
                "highlightedComments": item.get("highlightedComments")[0],
                "text": item.get("text"),
                "postedDate": item.get("postedDate"),
                "commentedDate": item.get("commentedDate"),
                "postUrl": item.get("postUrl"),
            }
            for item in raw_comments
        ]

        validated_output = CommentsOutput.parse_obj(output_data)
        return validated_output

    def fetch_profile_likes_by_username(self, username: str) -> LikesOutput:
        validated_input = UsernameInput(username=username)
        path = f"/get-profile-likes?username={validated_input.username}"
        decoded_data = self._make_api_request(path)
        items = decoded_data.get("data", {}).get("items", [])[:50]

        output_data = [
            {
                "text": item.get("text"),
                "action": item.get("action"),
                "postedDate": item.get("postedDate"),
                "totalReactionCount": item.get("totalReactionCount"),
                "commentsCount": item.get("commentsCount")
            }
            for item in items
        ]

        validated_output = LikesOutput.parse_obj(output_data)
        return validated_output
    
   
    
    def fetch_comments_by_post_urn(self, urn: str, count: int = 50) -> list[str]:
        comments = []
        page = 1
        fetched = 0
        pagination_token = ""

        while fetched < count:
            path = f"/get-profile-posts-comments?urn={urn}&sort=mostRelevant&page={page}"
            if pagination_token:
                path += f"&paginationToken={pagination_token}"

            try:
                decoded_data = self._make_api_request(path)
            except Exception as e:
                # Stop fetching if API errors out (optional: log error)
                break

            data = decoded_data.get("data", [])
            if not data:
                break  # No more data to fetch

            for item in data:
                text = item.get("text")
                if text:
                    comments.append(text)
                    fetched += 1
                    if fetched >= count:
                        break

            pagination_token = decoded_data.get("paginationToken")
            if not pagination_token:
                break  # No more pages

            page += 1

        return comments

# import http.client
# from datetime import datetime, timedelta
# import json
# from src.linkedin_extractor.config.config import settings
# from src.linkedin_extractor.schemas.profile import (
#     UsernameInput,
#     ProfileOutput,
#     PostOutput,
#     PostData,
#     CommentsOutput,
#     LikesOutput
# )

# class LinkedInAPIManager:
#     # def __init__(self):
#     #     self.headers = {
#     #         'x-rapidapi-key': settings.RAPIDAPI_KEY,
#     #         'x-rapidapi-host': settings.RAPIDAPI_HOST
#     #     }
#     #     self.api_calls = 0

#     # def get_credit_usage(self) -> int:
#     #     return self.api_calls

#     # def _make_api_request(self, path: str):
#     #     try:
#     #         self.api_calls += 1
#     #         conn = http.client.HTTPSConnection(settings.RAPIDAPI_HOST)
#     #         conn.request("GET", path, headers=self.headers)
#     #         res = conn.getresponse()
#     #         data = res.read()
#     #         conn.close()

#     #         decoded = json.loads(data.decode("utf-8"))
#     #         print(f"✅ API Call #{self.api_calls}: {path}")
#     #         print(json.dumps(decoded, indent=2))
#     #         return decoded
#     #     except Exception as e:
#     #         print(f"❌ API request failed at {path}: {e}")
#     #         raise ValueError(f"API request failed: {e}")
    
#     def __init__(self):
#         self.headers = {
#             'x-rapidapi-key': settings.RAPIDAPI_KEY,
#             'x-rapidapi-host': settings.RAPIDAPI_HOST
#         }
#         self.api_calls = 0
#         self.conn = http.client.HTTPSConnection(settings.RAPIDAPI_HOST)  # ✅ persistent connection

#     def get_credit_usage(self) -> int:
#         return self.api_calls

#     def _make_api_request(self, path: str):
#         try:
#             self.api_calls += 1
#             self.conn.request("GET", path, headers=self.headers)
#             res = self.conn.getresponse()

#             # Status code check (optional)
#             if res.status != 200:
#                 raise Exception(f"HTTP {res.status}: {res.reason}")

#             data = res.read()
#             decoded = json.loads(data.decode("utf-8"))

#             print(f"✅ API Call #{self.api_calls}: {path}")
#             print(json.dumps(decoded, indent=2))
#             return decoded

#         except Exception as e:
#             print(f"❌ API request failed at {path}: {e}")
#             # Reset connection in case it's broken
#             try:
#                 self.conn.close()
#             except:
#                 pass
#             self.conn = http.client.HTTPSConnection(settings.RAPIDAPI_HOST)
#             raise ValueError(f"API request failed: {e}")

#     def fetch_profile_data_by_username(self, username: str) -> ProfileOutput:
#         try:
#             validated_input = UsernameInput(username=username)
#             path = f"/?username={validated_input.username}"
#             decoded_data = self._make_api_request(path)

#             output_data = {
#                 "headline": decoded_data.get("headline"),
#                 "location": decoded_data.get("geo", {}).get("full"),
#                 "job_title": None,
#                 "company_name": None,
#             }

#             position = decoded_data.get("position", [])
#             first_position = position[0] if position else {}
#             output_data["job_title"] = first_position.get("title")
#             output_data["company_name"] = first_position.get("companyName")

#             return ProfileOutput(**output_data)
#         except Exception as e:
#             print(f"❌ fetch_profile_data_by_username failed: {e}")
#             raise

#     def fetch_recent_posts_by_username(self, username: str) -> PostOutput:
#         try:
#             validated_input = UsernameInput(username=username)
#             posts = []
#             reposts = []
#             start = 0
#             pagination_token = None
#             now = datetime.utcnow()
#             twelve_months_ago = now - timedelta(days=365)

#             while True:
#                 query = f"/get-profile-posts?username={validated_input.username}&start={start}"
#                 if pagination_token:
#                     query += f"&paginationToken={pagination_token}"

#                 decoded_data = self._make_api_request(query)
#                 raw_posts = decoded_data.get("data", [])
#                 pagination_token = decoded_data.get("nextToken")

#                 if not raw_posts:
#                     break

#                 stop_fetching = False
#                 for post in raw_posts:
#                     posted_at_str = post.get("postedDate")
#                     if not posted_at_str:
#                         continue

#                     try:
#                         posted_at = datetime.strptime(posted_at_str[:19], "%Y-%m-%d %H:%M:%S")
#                     except Exception:
#                         continue

#                     if posted_at < twelve_months_ago:
#                         stop_fetching = True
#                         break

#                     is_repost = "reposted" in post
#                     original_text = None

#                     if is_repost:
#                         reshared = post.get("resharedPost", {})
#                         original_text = reshared.get("text") or post.get("text")

#                     base_data = {
#                         "postedDate": posted_at_str,
#                         "totalReactionCount": post.get("totalReactionCount"),
#                         "commentsCount": post.get("commentsCount"),
#                         "urn": post.get("urn"),
#                         "text": post.get("text"),
#                         "original_text": original_text
#                     }

#                     if is_repost:
#                         reposts.append(PostData(**base_data))
#                     else:
#                         posts.append(PostData(**base_data))

#                 if stop_fetching or not pagination_token:
#                     break
#                 start += 50

#             return PostOutput(posts=posts, reposts=reposts)
#         except Exception as e:
#             print(f"❌ fetch_recent_posts_by_username failed: {e}")
#             raise

#     def fetch_profile_comments_by_username(self, username: str) -> CommentsOutput:
#         try:
#             validated_input = UsernameInput(username=username)
#             path = f"/get-profile-comments?username={validated_input.username}"
#             decoded_data = self._make_api_request(path)
#             raw_comments = decoded_data.get("data", [])

#             output_data = [
#                 {
#                     "highlightedComments": item.get("highlightedComments")[0],
#                     "text": item.get("text"),
#                     "postedDate": item.get("postedDate"),
#                     "commentedDate": item.get("commentedDate"),
#                     "postUrl": item.get("postUrl"),
#                 }
#                 for item in raw_comments
#             ]

#             return CommentsOutput.parse_obj(output_data)
#         except Exception as e:
#             print(f"❌ fetch_profile_comments_by_username failed: {e}")
#             raise

#     def fetch_profile_likes_by_username(self, username: str) -> LikesOutput:
#         try:
#             validated_input = UsernameInput(username=username)
#             path = f"/get-profile-likes?username={validated_input.username}"
#             decoded_data = self._make_api_request(path)
#             items = decoded_data.get("data", {}).get("items", [])[:50]

#             output_data = [
#                 {
#                     "text": item.get("text"),
#                     "action": item.get("action"),
#                     "postedDate": item.get("postedDate"),
#                     "totalReactionCount": item.get("totalReactionCount"),
#                     "commentsCount": item.get("commentsCount")
#                 }
#                 for item in items
#             ]

#             return LikesOutput.parse_obj(output_data)
#         except Exception as e:
#             print(f"❌ fetch_profile_likes_by_username failed: {e}")
#             raise

#     def fetch_comments_by_post_urn(self, urn: str, count: int = 50) -> list[str]:
#         try:
#             comments = []
#             page = 1
#             fetched = 0
#             pagination_token = ""

#             while fetched < count:
#                 path = f"/get-profile-posts-comments?urn={urn}&sort=mostRelevant&page={page}"
#                 if pagination_token:
#                     path += f"&paginationToken={pagination_token}"

#                 decoded_data = self._make_api_request(path)
#                 data = decoded_data.get("data", [])
#                 if not data:
#                     break

#                 for item in data:
#                     text = item.get("text")
#                     if text:
#                         comments.append(text)
#                         fetched += 1
#                         if fetched >= count:
#                             break

#                 pagination_token = decoded_data.get("paginationToken")
#                 if not pagination_token:
#                     break

#                 page += 1

#             return comments
#         except Exception as e:
#             print(f"❌ fetch_comments_by_post_urn failed: {e}")
#             return []
