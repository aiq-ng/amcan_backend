from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi import HTTPException
from .models import FeedItemCreate, FeedItemResponse
from .manager import get_feeds, create_feed_item
from .utils import validate_file, save_file
from modules.auth.utils import get_current_admin
from shared.response import success_response, error_response
from typing import List, Optional

router = APIRouter()

@router.get("/feeds")
async def get_feed(limit: int = 10, offset: int = 0):
    try:
        feeds = await get_feeds(limit, offset)
        # print("data gotten returning data", feeds)
        return success_response(data=feeds, message="Feeds retrieved successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.post("/create_feed", response_model=FeedItemResponse)
async def createss_feed_item(
    title: str = Form(...),
    content_type: str = Form(...),
    description: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    file: UploadFile = File(None),
    current_admin: dict = Depends(get_current_admin)
):
    print('creating feed item', title, content_type, description, content, file)
    try:
        # Manually construct FeedItemCreate from form data
        item = FeedItemCreate(
            title=title,
            content_type=content_type,
            description=description,
            content=content
        )
        print("checking content type", item.content_type)
        if item.content_type in ["video", "audio"]:
            if not file:
                raise ValueError("File required for video or audio")
            validate_file(file, item.content_type)
            file_path = await save_file(file)
        else:  # article
            if not item.content:
                raise ValueError("Content required for article")
            file_path = None
        print('creating feeding item')
        feed_item = await create_feed_item(item, current_admin["id"], file_path)
        print('feed item created', feed_item)
        return success_response(data=feed_item, message="Feed item created successfully")
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        return error_response(str(e), status_code=500)