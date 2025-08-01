import logging
from typing import List, Optional
from .models import BlogPostCreateModel, BlogPostResponseModel, MoodRecommendationModel
from .utils import db_connection, execute_query, fetch_all, fetch_one, upload_to_cloudinary, upload_image
import uuid
import json

logger = logging.getLogger(__name__)

async def create_blog_post(user_id: str, post_data) -> str:
    """Create a new blog post with optional Cloudinary upload for video/audio."""
    logger.debug(f"Creating blog post for user_id={user_id} with data={post_data}")
    async with db_connection() as conn:
        async with conn.transaction():
            post_id = f"blog_{uuid.uuid4().hex[:8]}"
            content_url = post_data.content_url
            thumbnail = post_data.thumbnail
            logger.debug(f"Generated post_id={post_id}")
            if post_data.content_type in ['video', 'audio']:
                logger.debug(f"Content type is {post_data.content_type}, checking for file upload")
                if not hasattr(content_url, 'read'):  # Check if it's a file object
                    logger.error("File upload required for video or audio")
                    raise ValueError("File upload required for video or audio")
                logger.debug("Uploading file to Cloudinary")
                thumbnail_url = await upload_image(thumbnail.file)
                content_url = await upload_to_cloudinary(content_url, post_data.content_type)
                logger.debug(f"Uploaded file, received content_url={content_url}")
            
            query = """
                INSERT INTO blog_posts (id, title, description, content_type, content_url, duration, mood_relevance, user_id, thumbnail_url)
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9)
                RETURNING id
            """
            logger.debug(f"Executing query to insert blog post: {query}")
            await execute_query(conn, query, (
                post_id, post_data.title, post_data.description, post_data.content_type, content_url,
                post_data.duration, json.dumps(post_data.mood_relevance), user_id, thumbnail_url["url"]
            ))
        logger.info(f"Blog post created with id={post_id}")
        return post_id

async def get_blog_posts_by_mood(user_id: str, limit: int = 5, offset: int = 0):
    """
    Fetch blog posts most relevant to the user's current mood.
    The mood_relevance column is stored as JSONB, e.g.:
    {"Sad": 0.4, "Calm": 0.9, "Angry": 0.0, "Happy": 0.3, "Manic": 0.1}
    This function fetches posts where the current mood exists in mood_relevance and its value > 0.
    """
    logger.debug(f"Fetching blog posts for user_id={user_id}, limit={limit}, offset={offset}")
    async with db_connection() as conn:
        # Get the user's current mood
        mood_query = """
            SELECT current_mood FROM mood_recommendations
            WHERE user_id = $1
            ORDER BY last_updated DESC
            LIMIT 1
        """
        mood_row = await fetch_one(conn, mood_query, (int(user_id),))
        if mood_row and mood_row.get("current_mood"):
            current_mood = mood_row["current_mood"]
        else:
            # If user does not have a mood, use a default mood that is likely to match (e.g., 'Happy')
            current_mood = "Happy"
            logger.info(f"No mood found for user_id={user_id}, using default mood '{current_mood}'")

        # For debugging: log all available moods in blog_posts
        debug_moods_query = "SELECT DISTINCT jsonb_object_keys(mood_relevance) as mood FROM blog_posts"
        available_moods = await fetch_all(conn, debug_moods_query)
        logger.debug(f"Available moods in blog_posts: {[row['mood'] for row in available_moods]}")

        # Query for posts matching the current mood
        # The comparison is correct: (bp.mood_relevance ? $1) checks if the mood exists as a key,
        # and (bp.mood_relevance->>$1)::float > 0 checks if its value is greater than zero.
        query = """
            SELECT bp.id, bp.title, bp.description, bp.content_type, bp.content_url, bp.duration, bp.mood_relevance, bp.created_at, bp.user_id, bp.thumbnail_url
            FROM blog_posts bp
            WHERE (bp.mood_relevance ? $1)
              AND (bp.mood_relevance->>$1)::float > 0
            ORDER BY (bp.mood_relevance->>$1)::float DESC
            LIMIT $2 OFFSET $3
        """
        logger.debug(f"Executing query to fetch blog posts by mood: {query} with mood={current_mood}")
        posts = await fetch_all(conn, query, (current_mood, limit, offset))
        logger.info(f"Fetched {len(posts)} blog posts for user_id={user_id} and mood={current_mood}")

        # If no posts found, log all blog_posts for inspection
        if not posts:
            logger.warning(f"No posts found for mood '{current_mood}'. Fetching all blog_posts for debugging.")
            all_posts_query = """
                SELECT id, title, mood_relevance FROM blog_posts
                ORDER BY created_at DESC
                LIMIT 10
            """
            all_posts = await fetch_all(conn, all_posts_query)
            logger.debug(f"Sample blog_posts: {all_posts}")

        return [dict(post) for post in posts]

async def update_user_mood(user_id: str, mood: str) -> None:
    """Update the user's current mood."""
    logger.debug(f"Updating mood for user_id={user_id} to mood={mood}")
    async with db_connection() as conn:
        # Use UPSERT to avoid duplicate key errors
        upsert_query = """
            INSERT INTO mood_recommendations (id, user_id, current_mood, last_updated)
            VALUES ($1, $1, $2, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE
            SET current_mood = EXCLUDED.current_mood,
                last_updated = EXCLUDED.last_updated
        """
        await execute_query(conn, upsert_query, (int(user_id), mood))
        logger.info(f"Upserted mood for user_id={user_id} to mood={mood}")


async def get_all_blog_posts(limit: int = 20, offset: int = 0) -> List:
    """Fetch all blog posts with pagination."""
    logger.debug(f"Fetching all blog posts, limit={limit}, offset={offset}")
    async with db_connection() as conn:
        query = """
            SELECT id, title, description, content_type, content_url, duration, mood_relevance, created_at, user_id, thumbnail_url
            FROM blog_posts
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        posts = await fetch_all(conn, query, (limit, offset))
        logger.info(f"Fetched {len(posts)} blog posts")
        return [dict(post) for post in posts]

async def update_blog_post(post_id: str, user_id: str, update_data) -> Optional[str]:
    """Update an existing blog post. Only the owner can update."""
    print("********** blog post update data", update_data)
    logger.debug(f"Updating blog post id={post_id} for user_id={user_id} with data={update_data}")
    async with db_connection() as conn:
        # Check ownership
        check_query = "SELECT user_id FROM blog_posts WHERE id = $1"
        owner = await fetch_one(conn, check_query, (post_id,))
        if not owner or str(owner["user_id"]) != str(user_id):
            logger.warning(f"User {user_id} not authorized to update post {post_id}")
            return None

        # Prepare update fields and values
        fields = []
        values = []
        if update_data["title"] is not None:
            fields.append("title")
            values.append(update_data['title'])
        if update_data["description"] is not None:
            fields.append("description")
            values.append(update_data['description'])
        if update_data["content_type"] is not None:
            fields.append("content_type")
            values.append(update_data['content_type'])
        if update_data["content_url"] is not None:
            fields.append("content_url")
            values.append(update_data['content_url'])
        if update_data["duration"] is not None:
            fields.append("duration")
            values.append(update_data['duration'])
        if update_data["mood_relevance"] is not None:
            fields.append("mood_relevance")
            values.append(json.dumps(update_data['mood_relevance']))
        if update_data["thumbnail"] is not None:
            fields.append("thumbnail_url")
            thumbnail = update_data["thumbnail"]
            if hasattr(thumbnail, "file"):  # It's a file object
                thumbnail_url = await upload_image(thumbnail.file)
                values.append(thumbnail_url["url"])
            elif isinstance(thumbnail, str) and thumbnail.startswith("http"):
                values.append(thumbnail)
            else:
                values.append(None)

        if not fields:
            logger.info(f"No fields to update for post {post_id}")
            return post_id

        # Build the SET clause with correct parameter placeholders
        set_clause = ", ".join([f"{field} = ${idx+2}" for idx, field in enumerate(fields)])
        update_query = f"""
            UPDATE blog_posts
            SET {set_clause}
            WHERE id = $1
            RETURNING id
        """
        params = [post_id] + values
        logger.debug(f"Executing update query: {update_query} with values {params}")
        result = await fetch_one(conn, update_query, params)
        if result:
            logger.info(f"Blog post {post_id} updated successfully")
            return result["id"]
        logger.error(f"Failed to update blog post {post_id}")
        return None

