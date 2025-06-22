from .models import FeedItemCreate, FeedItemResponse
from shared.db import db
import os
import mimetypes
from typing import Optional

async def create_feed_item(item: FeedItemCreate, user_id: int, file_path: Optional[str] = None) -> dict:
    print('creatinf manager hit')
    
    async with db.get_connection() as conn:
        print('creating manager hit')
        url = f"/uploads/{os.path.basename(file_path)}" if file_path else None
        row = await conn.fetchrow(
            """
            INSERT INTO feed_items (title, content_type, url, content, description, created_by)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, title, content_type, content, description, created_at, created_by
            """,
            item.title,
            item.content_type,
            url,
            item.content if item.content_type == "article" else None,
            item.description,
            user_id
        )
        print('creatinf manager hit')
        result = dict(row)
        result['created_at'] = result['created_at'].isoformat()
        return result

async def get_feeds(limit: int = 10, offset: int = 0) -> list:
    async with db.get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT id, title, content_type, content, description, created_at, created_by
            FROM feed_items ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset
        )
        if not rows:
            return []
        else:
            return [dict(row) for row in rows]
        # return [dict(row) for row in rows]