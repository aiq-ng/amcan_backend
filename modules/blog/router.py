import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from .models import BlogPostCreateModel, BlogPostResponseModel, MoodRecommendationModel
from .manager import create_blog_post, get_blog_posts_by_mood, update_user_mood, get_all_blog_posts
from .utils import db_connection
from typing import List
from asyncpg import Connection
import json
from modules.auth.utils import get_current_user
from shared.response import success_response, error_response
from .manager import update_blog_post

# Configure logging
logger = logging.getLogger("blog_router")
logging.basicConfig(level=logging.INFO)

router = APIRouter()

async def get_db() -> Connection:
    async with db_connection() as conn:
        yield conn

@router.post("/posts")
async def create_post(
    user_id: str = Depends(get_current_user),
    title: str = Form(...),
    description: str = Form(...),
    content_type: str = Form(...),
    content_url: str = Form(...),
    thumbnail: UploadFile = File(None),
    duration: int = Form(None),
    mood_relevance: str = Form(...),
    file: UploadFile = File(None)
):
    logger.info(f"Received create_post request: user_id={user_id['id']}, title={title}, content_type={content_type}")
    try:
        mood_relevance_data = json.loads(mood_relevance)
        logger.debug(f"Parsed mood_relevance: {mood_relevance_data}")
    except Exception as e:
        logger.error(f"Failed to parse mood_relevance: {mood_relevance}, error: {e}")
        raise HTTPException(status_code=400, detail="Invalid mood_relevance JSON")

    post_data = BlogPostCreateModel(
        title=title,
        description=description,
        content_type=content_type,
        content_url=content_url,
        duration=duration,
        mood_relevance=mood_relevance_data,
        thumbnail=thumbnail
    )

    try:
        if post_data.content_type in ['video', 'audio']:
            if not file:
                logger.warning("File upload required for video or audio but not provided")
                raise HTTPException(status_code=400, detail="File upload required for video or audio")
            post_data.content_url = file.file
            logger.info(f"File uploaded for {post_data.content_type}")
        elif post_data.content_type == 'article':
            if file:
                logger.warning("File upload not allowed for articles")
                raise HTTPException(status_code=400, detail="File upload not allowed for articles")
            if not post_data.content_url.strip().startswith('<'):
                logger.warning("Invalid HTML content for article")
                raise HTTPException(status_code=400, detail="Invalid HTML content")
        
        logger.info(f"Creating blog post for user_id={user_id['id']}")
        post_id = await create_blog_post(user_id['id'], post_data)
        logger.info(f"Blog post created successfully: post_id={post_id}")
        return success_response(data=post_id, message="Blog post created successfully")
    except ValueError as e:
        logger.error(f"ValueError while creating post: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error while creating post: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating post: {str(e)}")

@router.get("/posts")
async def get_mood_based_posts(
    user_id: str,
    limit: int = 5,
    offset: int = 0,
    db: Connection = Depends(get_db)
):
    logger.info(f"Fetching posts for user_id={user_id}, limit={limit}, offset={offset}")
    try:
        posts = await get_blog_posts_by_mood(user_id, limit, offset)
        logger.info(f"Fetched {len(posts) if posts else 0} posts for user_id={user_id}")
        if not posts:
            logger.warning(f"No posts found for user_id={user_id} and current mood")
            raise HTTPException(status_code=404, detail="No posts found for current mood")
        return success_response(data=posts, message="Posts fetched successfully")
    except Exception as e:
        logger.error(f"Error fetching posts for user_id={user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching posts: {str(e)}")

@router.post("/mood", response_model=None)
async def update_mood(
    user_id: str,
    mood: MoodRecommendationModel,
    db: Connection = Depends(get_db)
):
    logger.info(f"Updating mood for user_id={user_id} to {mood.current_mood}")
    try:
        response = await update_user_mood(user_id, mood.current_mood)
        logger.info(f"Mood updated successfully for user_id={user_id}")
        return success_response(data=response, message="Mood updated successfully")
    except Exception as e:
        logger.error(f"Error updating mood for user_id={user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating mood: {str(e)}")


@router.get("/posts/all")
async def get_all_posts(
    limit: int = 20,
    offset: int = 0,
    db: Connection = Depends(get_db)
):
    logger.info(f"Fetching all blog posts, limit={limit}, offset={offset}")
    try:
        posts = await get_all_blog_posts(limit, offset)
        logger.info(f"Fetched {len(posts) if posts else 0} blog posts")
        if not posts:
            logger.warning("No blog posts found")
            raise HTTPException(status_code=404, detail="No blog posts found")
        return success_response(data=posts, message="All blog posts fetched successfully")
    except Exception as e:
        logger.error(f"Error fetching all blog posts: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching all blog posts: {str(e)}")
    
@router.put("/posts/{post_id}")
async def update_post(
    post_id: str,
    user_id: str = Depends(get_current_user),
    title: str = Form(None),
    description: str = Form(None),
    content_type: str = Form(None),
    content_url: str = Form(None),
    thumbnail: UploadFile = File(None),
    duration: int = Form(None),
    mood_relevance: str = Form(None),
    file: UploadFile = File(None)
):
    logger.info(f"Received update_post request: post_id={post_id}, user_id={user_id['id']}")
    try:
        mood_relevance_data = None
        if mood_relevance:
            try:
                mood_relevance_data = json.loads(mood_relevance)
                logger.debug(f"Parsed mood_relevance: {mood_relevance_data}")
            except Exception as e:
                logger.error(f"Failed to parse mood_relevance: {mood_relevance}, error: {e}")
                raise HTTPException(status_code=400, detail="Invalid mood_relevance JSON")

        update_data = {
            "title": title,
            "description": description,
            "content_type": content_type,
            "content_url": content_url,
            "duration": duration,
            "mood_relevance": mood_relevance_data,
            "thumbnail": thumbnail
        }

        # Remove keys with None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        print("*****printing update data****", update_data)
        if update_data.get("content_type") in ['video', 'audio']:
            if file:
                update_data["content_url"] = file.file
                logger.info(f"File uploaded for {update_data['content_type']}")
        elif update_data.get("content_type") == 'article':
            if file:
                logger.warning("File upload not allowed for articles")
                raise HTTPException(status_code=400, detail="File upload not allowed for articles")
            if content_url and not content_url.strip().startswith('<'):
                logger.warning("Invalid HTML content for article")
                raise HTTPException(status_code=400, detail="Invalid HTML content")

        # Import here to avoid circular import

        logger.info(f"Updating blog post: post_id={post_id}")
        updated_post = await update_blog_post(post_id, user_id['id'], update_data)
        logger.info(f"Blog post updated successfully: post_id={post_id}")
        return success_response(data=updated_post, message="Blog post updated successfully")
    except ValueError as e:
        logger.error(f"ValueError while updating post: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error while updating post: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")


          