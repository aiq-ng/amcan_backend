
from typing import List, Optional
from .models import ProductListingModel, ProductDetailModel, ReviewResponseModel, ReviewCreateModel
from .utils import fetch_all, fetch_one, execute_query
from shared.db import db as db_connection
import json

async def get_products(category_id: Optional[str] = None, limit: int = 10, offset: int = 0, 
                      sort_by: str = 'id', sort_order: str = 'asc', q: Optional[str] = None, 
                      is_high_demand: bool = False) -> List[ProductListingModel]:
    """Fetch a list of products with filtering, pagination, and sorting."""
    async with db_connection.get_connection() as conn:
        query = """
            SELECT p.id, p.name, p.price, p.image_urls[1] AS image_url, 
                   p.average_rating, p.total_reviews, c.name AS category
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        """
        params = []
        param_count = 0
        
        if category_id:
            param_count += 1
            query += f" AND p.category_id = ${param_count}"
            params.append(category_id)
        if q:
            param_count += 1
            query += f" AND p.name ILIKE ${param_count}"
            params.append(f"%{q}%")
        if is_high_demand:
            query += " AND p.is_high_demand = TRUE"
            # No parameter needed for boolean check
        
        query += f" ORDER BY {sort_by} {sort_order}"
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)
        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)

        products = await fetch_all(conn, query, tuple(params))
        print("products", products)
        return [dict(row) for row in products]

async def get_product_by_id(product_id: str) -> Optional[ProductDetailModel]:
    """Fetch detailed information for a single product."""
    async with db_connection.get_connection() as conn:
        query = """
            SELECT p.id, p.name, p.description, p.price, p.image_urls, 
                   p.average_rating, p.total_reviews, p.key_benefits, p.specifications, c.name AS category
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = $1
        """
        product = await fetch_one(conn, query, (product_id,))
        if product and isinstance(product.get("specifications"), str):
            try:
                product["specifications"] = json.loads(product["specifications"])
            except Exception:
                product["specifications"] = []
        return ProductDetailModel(**product) if product else None

async def get_product_reviews(product_id: str, limit: int = 5, offset: int = 0):
    """Fetch reviews for a specific product with pagination."""
    async with db_connection.get_connection() as conn:
        query = """
            SELECT r.id, r.rating, r.comment, u.first_name || ' ' || u.last_name AS user_name, r.created_at
            FROM reviews r
            JOIN users u ON r.user_id = u.id 
            WHERE r.product_id = $1 
            ORDER BY r.created_at DESC
            LIMIT $2 OFFSET $3
        """
        try:
            reviews = await fetch_all(conn, query, (product_id, limit, offset))
            print("reviews", reviews)
            return [dict(row) for row in reviews]
        except Exception as e:
            # Re-raising with a more informative message if possible
            print(f"Error fetching reviews: {e}")
            raise RuntimeError(f"Error fetching reviews: {e}")

async def create_product_review(product_id: str, user_id: str, rating: int, comment: str) -> str:
    """Insert a new review and update product average_rating and total_reviews."""
    print(f"create_product_review called with product_id={product_id}, user_id={user_id}, rating={rating}, comment={comment}")
    async with db_connection.get_connection() as conn:
        # Start transaction
        async with conn.transaction():
            try:
                # Insert review
                review_id = "rev_" + str(hash(f"{product_id}{user_id}{rating}{comment}"))[-8:]  # Simple ID generation
                print(f"Generated review_id: {review_id}")
                query = """
                    INSERT INTO reviews (id, product_id, user_id, rating, comment)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id, product_id, user_id, rating, comment, created_at
                """
                try:
                    print(f"Executing review insert query with params: {review_id}, {product_id}, {user_id}, {rating}, {comment}")
                    result = await execute_query(conn, query, (review_id, product_id, user_id, rating, comment))
                    print(f"Insert result: {result}")
                    # if not result:
                    #     print("Review already exists or insertion failed")
                    #     raise ValueError("Review already exists or insertion failed")
                except Exception as e:
                    print(f"Exception during review insert: {e}")
                    raise RuntimeError(f"Failed to insert review: {e}")
            except Exception as e:
                print(f"Exception occurred while creating product review: {e}")
                raise

            # Update product stats
            query = """
                UPDATE products p
                SET total_reviews = total_reviews + 1,
                    average_rating = (
                        SELECT COALESCE(AVG(r.rating), 0)
                        FROM reviews r
                        WHERE r.product_id = p.id
                    )
                WHERE p.id = $1
            """
            await execute_query(conn, query, (product_id,))
        return review_id
