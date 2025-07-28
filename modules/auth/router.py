from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from .models import UserCreate, UserResponse, UserUpdate
from .manager import AuthManager
from .utils import get_current_admin, get_current_user
from shared.response import success_response, error_response



router = APIRouter()
print('[AUTH] Auth router initialized')

@router.post("/register")
async def register(user: UserCreate):
    print(f"[AUTH] /register called with user: {user.email}")
    try:
        user_data = await AuthManager.register(user)
        return success_response(data=user_data, message="User registered successfully")
    except ValueError as e:
        print(f"[AUTH] /register error: {e}")
        return error_response(str(e), status_code=400)

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):

    try:
        token = await AuthManager.login(form_data.username, form_data.password)
        return success_response(data={"access_token": token, "token_type": "bearer"})
    except ValueError as e:
        print(f"[AUTH] /login error: {e}")
        return error_response(str(e), status_code=401)

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    print(f"[AUTH] /me called for user: {current_user.get('email', 'unknown')}")
    print("*** current user", current_user)
    return success_response(data=current_user, message="User details retrieved")

    # INSERT_YOUR_CODE
@router.get("/users")
async def get_all_users(current_admin: dict = Depends(get_current_admin)):
    """
    Endpoint to retrieve all users. Only accessible by admins.
    """
    try:
        users = await AuthManager.get_all_users()
        return success_response(data=users, message="All users retrieved successfully")
    except Exception as e:
        print(f"[AUTH] /users error: {e}")
        return error_response("Failed to retrieve users", status_code=500)
    
        # INSERT_YOUR_CODE

@router.put("/users/{user_id}")
async def update_user(user_id: int, update: UserUpdate, current_user: dict = Depends(get_current_user)):
    try:
        updated_user = await AuthManager.update_user(user_id, update.dict(exclude_unset=True), current_user)
        return success_response(data=updated_user, message="User updated successfully")
    except ValueError as e:
        return error_response(str(e), status_code=403)
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_admin)):
    try:
        deleted_user = await AuthManager.delete_user(user_id, current_user)
        return success_response(data=deleted_user, message="User deleted successfully")
    except ValueError as e:
        return error_response(str(e), status_code=403)
    except Exception as e:
        return error_response(str(e), status_code=500)

