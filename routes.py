from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user, create_user
from db_operations import insert_post, select_posts, create_like, delete_like, get_post_like_count, get_like_stats, \
    fetch_user, fetch_users
from models import Post, User, RowCreationResult, PostCreate, UserCreate

router = APIRouter(prefix='/api')
RESERVED_USERNAMES = (
    'me',
)


@router.post('/users/')
async def signup(user: UserCreate):
    if user.username in RESERVED_USERNAMES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='This username is not allowed')
    success = await create_user(user.username, user.password)
    if not success:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='This username is already taken')
    return {'username': user.username}


@router.get('/users/', response_model=list[User])
async def get_users():
    return await fetch_users()


@router.get('/users/me/', response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get('/users/{username}', response_model=User)
async def get_user(username: str):
    return await fetch_user(username)


@router.post('/posts/')
async def create_post(post: PostCreate, current_user: User = Depends(get_current_user)):
    post_id = await insert_post(current_user.id, post.title, post.body)
    if post_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Post with this title already exists')
    return {'id': post_id}


@router.get('/posts/{post_id}/', response_model=Post)
async def get_post(post_id: int):
    posts = await select_posts([post_id])
    if not posts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    post = posts[0]
    post.like_count = await get_post_like_count(post.id)
    return post


@router.get('/posts/', response_model=list[Post])
async def get_all_posts():
    result = await select_posts()
    return result


@router.post('/posts/{post_id}/like/')
async def like_post(post_id: int, current_user: User = Depends(get_current_user)):
    result: RowCreationResult = await create_like(current_user.id, post_id)
    if result == RowCreationResult.FOREIGN_KEY_VIOLATION:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    elif result == RowCreationResult.UNIQUE_VIOLATION:
        response = 'Already liked'
    elif result == RowCreationResult.CREATED:
        response = 'OK'
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return response


@router.delete('/posts/{post_id}/like/')
async def unlike_post(post_id: int, current_user: User = Depends(get_current_user)):
    success: bool = await delete_like(current_user.id, post_id)
    return 'OK' if success else 'Like not found'


@router.get('/analytics/likes/')
async def get_like_analytics(date_from: date, date_to: date):
    if date_from > date_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='date_from must not be greater than date_to')
    return await get_like_stats(date_from, date_to)
