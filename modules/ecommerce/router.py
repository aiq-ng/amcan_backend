
from fastapi import APIRouter, Depends, HTTPException
from .models import ProductListingModel, ProductDetailModel, ReviewCreateModel, ReviewResponseModel
from .manager import get_products, get_product_by_id, get_product_reviews, create_product_review
from .utils import db_connection
from typing import List, Optional
from asyncpg import Connection
from shared.db import db
from modules.auth.utils import get_current_user
from shared.response import success_response, error_response



router = APIRouter()



@router.get("/products")
async def list_products(
    category_id: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "id",
    sort_order: str = "asc",
    q: Optional[str] = None,
    is_high_demand: bool = False
):
    try:
        products = await get_products(category_id, limit, offset, sort_by, sort_order, q, is_high_demand)
        return success_response(data=products, message="products fectched successfully")  
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@router.get("/products/{product_id}")
async def get_product(product_id: str):
    product = await get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return success_response(data=product, message="product fectched successfully")

@router.get("/products/{product_id}/reviews")
async def list_reviews(product_id: str, limit: int = 5, offset: int = 0):
    try:
        reviews = await get_product_reviews(product_id, limit, offset)
        return success_response(data=reviews, message="reviews fetch successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching reviews: {str(e)}")

@router.post("/products/{product_id}/reviews")
async def create_review(
    product_id: str,
    review: ReviewCreateModel,
    user: Connection = Depends(get_current_user)
):
    try:
        review_id = await create_product_review(product_id, user["id"], review.rating, review.comment)
        return review_id
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating review: {str(e)}")
