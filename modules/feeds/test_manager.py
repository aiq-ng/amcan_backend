import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from modules.feeds.manager import create_feed_item, get_feeds
from modules.feeds.models import FeedItemCreate
from datetime import datetime

@pytest_asyncio.fixture
def article_data():
    return FeedItemCreate(
        title="Test Article",
        content_type="article",
        content="This is an article.",
        description="A test article."
    )

@pytest_asyncio.fixture
def video_data():
    return FeedItemCreate(
        title="Test Video",
        content_type="video",
        url="/uploads/test.mp4",
        description="A test video."
    )

@pytest.mark.asyncio
@patch("modules.feeds.manager.db.get_connection")
async def test_create_feed_item_article_success(mock_get_conn, article_data):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {
        "id": 1,
        "title": article_data.title,
        "content_type": article_data.content_type,
        "content": article_data.content,
        "description": article_data.description,
        "created_at": datetime.now(),
        "created_by": 1
    }
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await create_feed_item(article_data, user_id=1)
    assert result["title"] == article_data.title
    assert result["content_type"] == "article"
    assert result["content"] == article_data.content

@pytest.mark.asyncio
@patch("modules.feeds.manager.db.get_connection")
async def test_create_feed_item_video_success(mock_get_conn, video_data):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {
        "id": 2,
        "title": video_data.title,
        "content_type": video_data.content_type,
        "content": None,
        "description": video_data.description,
        "created_at": datetime.now(),
        "created_by": 1
    }
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await create_feed_item(video_data, user_id=1, file_path="/some/path/test.mp4")
    assert result["title"] == video_data.title
    assert result["content_type"] == "video"
    assert result["content"] is None

@pytest.mark.asyncio
@patch("modules.feeds.manager.db.get_connection")
async def test_get_feeds_success(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = [
        {"id": 1, "title": "Test Article", "content_type": "article", "content": "This is an article.", "description": "A test article.", "created_at": datetime.now(), "created_by": 1}
    ]
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await get_feeds()
    assert isinstance(result, list)
    assert result[0]["title"] == "Test Article"

@pytest.mark.asyncio
@patch("modules.feeds.manager.db.get_connection")
async def test_get_feeds_empty(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await get_feeds()
    assert result == [] 