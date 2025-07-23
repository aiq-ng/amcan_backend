import logging
from typing import List, Optional
from .models import BlogPostCreateModel, BlogPostResponseModel, MoodRecommendationModel
from .utils import db_connection, execute_query, fetch_all, fetch_one, upload_to_cloudinary
import uuid
import json

logger = logging.getLogger(__name__)

async def create_blog_post(user_id: str, post_data: BlogPostCreateModel) -> str:
    """Create a new blog post with optional Cloudinary upload for video/audio."""
    logger.debug(f"Creating blog post for user_id={user_id} with data={post_data}")
    async with db_connection() as conn:
        async with conn.transaction():
            post_id = f"blog_{uuid.uuid4().hex[:8]}"
            content_url = post_data.content_url
            logger.debug(f"Generated post_id={post_id}")
            if post_data.content_type in ['video', 'audio']:
                logger.debug(f"Content type is {post_data.content_type}, checking for file upload")
                if not hasattr(content_url, 'read'):  # Check if it's a file object
                    logger.error("File upload required for video or audio")
                    raise ValueError("File upload required for video or audio")
                logger.debug("Uploading file to Cloudinary")
                content_url = await upload_to_cloudinary(content_url, post_data.content_type)
                logger.debug(f"Uploaded file, received content_url={content_url}")
            
            query = """
                INSERT INTO blog_posts (id, title, description, content_type, content_url, duration, mood_relevance, user_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
                RETURNING id
            """
            logger.debug(f"Executing query to insert blog post: {query}")
            await execute_query(conn, query, (
                post_id, post_data.title, post_data.description, post_data.content_type, content_url,
                post_data.duration, json.dumps(post_data.mood_relevance), user_id
            ))
        logger.info(f"Blog post created with id={post_id}")
        return post_id

async def get_blog_posts_by_mood(user_id: str, limit: int = 5, offset: int = 0):
    """Fetch blog posts recommended based on user's current mood."""
    logger.debug(f"Fetching blog posts for user_id={user_id}, limit={limit}, offset={offset}")
    async with db_connection() as conn:
        query = """
            SELECT bp.id, bp.title, bp.description, bp.content_type, bp.content_url, bp.duration, bp.mood_relevance, bp.created_at, bp.user_id
            FROM blog_posts bp
            JOIN mood_recommendations mr ON mr.user_id = $1
            WHERE (bp.mood_relevance ? mr.current_mood)
              AND (bp.mood_relevance->>mr.current_mood)::float > 0
              AND mr.current_mood = (
                SELECT current_mood FROM mood_recommendations WHERE user_id = $1
                ORDER BY last_updated DESC LIMIT 1
              )
            ORDER BY (bp.mood_relevance->>mr.current_mood)::float DESC
            LIMIT $2 OFFSET $3
        """
        logger.debug(f"Executing query to fetch blog posts by mood: {query}")
        posts = await fetch_all(conn, query, (int(user_id), limit, offset))
        logger.info(f"Fetched {len(posts)} blog posts for user_id={user_id}")
        if not posts:
            logger.warning(f"No posts found for user_id={user_id} and current mood")
            return []
        return [dict(post) for post in posts]

async def update_user_mood(user_id: str, mood: str) -> None:
    """Update the user's current mood."""
    logger.debug(f"Updating mood for user_id={user_id} to mood={mood}")
    async with db_connection() as conn:
        query = """
            INSERT INTO mood_recommendations (id, user_id, current_mood)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE
            SET current_mood = EXCLUDED.current_mood, last_updated = CURRENT_TIMESTAMP
        """
        logger.debug(f"Executing query to update user mood: {query}")
        await execute_query(conn, query, (f"mood_{user_id}", int(user_id), mood))
        logger.info(f"Updated mood for user_id={user_id} to mood={mood}")
        


async def get_all_blog_posts(limit: int = 20, offset: int = 0) -> List:
    """Fetch all blog posts with pagination."""
    logger.debug(f"Fetching all blog posts, limit={limit}, offset={offset}")
    async with db_connection() as conn:
        query = """
            SELECT id, title, description, content_type, content_url, duration, mood_relevance, created_at, user_id
            FROM blog_posts
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        posts = await fetch_all(conn, query, (limit, offset))
        logger.info(f"Fetched {len(posts)} blog posts")
        return [dict(post) for post in posts]