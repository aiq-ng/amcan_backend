from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from .models import UserCreate, UserResponse
from .manager import AuthManager
from .utils import get_current_user
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

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    print(f"[AUTH] /me called for user: {current_user.get('email', 'unknown')}")
    return success_response(data=current_user, message="User details retrieved")