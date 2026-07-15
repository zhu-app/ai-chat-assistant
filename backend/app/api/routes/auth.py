from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import create_access_token, hash_password, verify_password
from app.core.dependencies import get_current_user, get_user_repository
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix='/api/auth', tags=['auth'])


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: str
    username: str


class UserInfoResponse(BaseModel):
    user_id: str
    username: str


class UserListItem(BaseModel):
    user_id: str
    username: str
    created_at: str


@router.get('/users', response_model=list[UserListItem])
def list_users(
    repo: UserRepository = Depends(get_user_repository),
    user_id: str = Depends(get_current_user),
):
    """查看所有已注册用户（需要登录）"""
    users = repo.list_users()
    return [
        UserListItem(user_id=u.id, username=u.username, created_at=u.created_at)
        for u in users
    ]


@router.post('/register', response_model=AuthResponse)
def register(payload: RegisterRequest, repo: UserRepository = Depends(get_user_repository)):
    username = payload.username.strip().lower()
    if len(username) < 2:
        raise HTTPException(status_code=400, detail='用户名至少 2 个字符')
    if len(payload.password) < 4:
        raise HTTPException(status_code=400, detail='密码至少 4 个字符')

    existing = repo.get_by_username(username)
    if existing:
        raise HTTPException(status_code=409, detail='用户名已存在')

    user = repo.create(username, hash_password(payload.password))
    token = create_access_token({'sub': user.id, 'username': user.username})
    return AuthResponse(token=token, user_id=user.id, username=user.username)


@router.post('/login', response_model=AuthResponse)
def login(payload: LoginRequest, repo: UserRepository = Depends(get_user_repository)):
    username = payload.username.strip().lower()
    user = repo.get_by_username(username)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='用户名或密码错误')

    token = create_access_token({'sub': user.id, 'username': user.username})
    return AuthResponse(token=token, user_id=user.id, username=user.username)


@router.post('/guest', response_model=AuthResponse)
def guest_login(repo: UserRepository = Depends(get_user_repository)):
    """游客模式：自动创建临时用户，无需注册即可使用。"""
    import uuid

    guest_id = str(uuid.uuid4())[:8]
    username = f'游客_{guest_id}'
    password = str(uuid.uuid4())

    user = repo.create(username, hash_password(password))
    token = create_access_token({'sub': user.id, 'username': user.username})
    return AuthResponse(token=token, user_id=user.id, username=user.username)


@router.get('/me', response_model=UserInfoResponse)
def get_me(
    user_id: str = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repository),
):
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')
    return UserInfoResponse(user_id=user.id, username=user.username)