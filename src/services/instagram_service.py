import logging
from insta import get_insta_data, get_insta_posts

logger = logging.getLogger(__name__)

class InstagramService:
    async def build_gpt_input(self, username, extra_info):
        """Build input data for GPT analysis"""
        try:
            profile_data = await get_insta_data(username)
            posts_data = await get_insta_posts(username)

            if not profile_data:
                raise Exception("Error getting profile data from Instagram")
                
            if not posts_data:
                logger.warning(f"Warning: Could not get posts data for {username}. Continuing with limited information.")

            # Process post data (up to 5 non-video posts)
            recent_posts = []
            
            if posts_data and 'data' in posts_data:
                count = 0
                for post in posts_data.get("data", []):
                    if count >= 5:
                        break
                    if post.get("media_type") != "VIDEO":
                        recent_posts.append({
                            "image_description": post.get("caption", "")[:100] or "No image description",
                            "caption": post.get("caption", ""),
                            "hashtags": [tag for tag in post.get("caption", "").split() if tag.startswith("#")],
                            "comments": []  # API doesn't provide comments yet
                        })
                        count += 1

            # Get biography and profile picture
            bio = ""
            profile_pic_url = ""
            
            if isinstance(profile_data, dict):
                if 'biography' in profile_data:
                    bio = profile_data.get('biography', '')
                elif 'data' in profile_data and 'user' in profile_data['data'] and 'biography' in profile_data['data']['user']:
                    bio = profile_data['data']['user'].get('biography', '')
                
                if 'profile_pic_url_hd' in profile_data:
                    profile_pic_url = profile_data.get('profile_pic_url_hd', '')
                elif 'data' in profile_data and 'user' in profile_data['data'] and 'profile_pic_url_hd' in profile_data['data']['user']:
                    profile_pic_url = profile_data['data']['user'].get('profile_pic_url_hd', '')
                    
            # Get followers and following counts
            followers = 0
            following = 0
            
            if isinstance(profile_data, dict):
                if 'edge_followed_by' in profile_data and 'count' in profile_data['edge_followed_by']:
                    followers = profile_data['edge_followed_by']['count']
                elif 'data' in profile_data and 'user' in profile_data['data'] and 'edge_followed_by' in profile_data['data']['user']:
                    followers = profile_data['data']['user']['edge_followed_by']['count']
                    
                if 'edge_follow' in profile_data and 'count' in profile_data['edge_follow']:
                    following = profile_data['edge_follow']['count']
                elif 'data' in profile_data and 'user' in profile_data['data'] and 'edge_follow' in profile_data['data']['user']:
                    following = profile_data['data']['user']['edge_follow']['count']

            return {
                "structured_data": {
                    "name": extra_info.get("name", ""),
                    "username": username,
                    "birth_year": extra_info.get("birth_year", 0),
                    "age_estimate": extra_info.get("age_estimate", 0),
                    "gender": extra_info.get("gender", ""),
                    "city": extra_info.get("city", ""),
                    "job": extra_info.get("job", ""),
                    "notable_event": extra_info.get("notable_event", ""),
                    "relationship": extra_info.get("relationship", "")
                },
                "profile": {
                    "bio": bio,
                    "profile_picture_description": profile_pic_url
                },
                "account_stats": {
                    "followers": followers,
                    "following": following
                },
                "recent_posts": recent_posts,
                "stories": [],  # Not supported yet
                "visual_style": "Visual style derived from posts and profile picture"
            }
        except Exception as e:
            logger.error(f"Error in build_gpt_input: {str(e)}")
            raise

# Create global Instagram service instance
instagram_service = InstagramService() 