from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from db_operations import insert_user, fetch_user, update_last_visit, update_last_login
from models import Token, UserAuth

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

# Generate your own SECRET_KEY and keep it secret for use in production.
# To get a string like this run:
# openssl rand -hex 32
SECRET_KEY = 'ecf998039f7d180e93bdcda768fc762b51132ebb71287e2dc8fb39230f4d5cfb'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 300


def get_unauthorized_exception(detail: str):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={'WWW-Authenticate': 'Bearer'},
    )


auth_router = APIRouter()


def verify_password(password, password_hash):
    return pwd_context.verify(password, password_hash)


def get_password_hash(password):
    return pwd_context.hash(password)


async def create_user(username: str, password: str) -> bool:
    password_hash = get_password_hash(password)
    return await insert_user(username, password_hash)


async def authenticate_user(username: str, password: str) -> Optional[UserAuth]:
    user_auth: UserAuth = await fetch_user(username)
    if not user_auth:
        return None
    if not verify_password(password, user_auth.password_hash):
        return None
    return user_auth


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserAuth:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise get_unauthorized_exception('Token expired')
    except JWTError:
        raise get_unauthorized_exception('Could not validate credentials')
    username: str = payload.get('sub')
    if username is None:
        raise get_unauthorized_exception('Could not validate credentials')
    user_auth: UserAuth = await fetch_user(username)
    if user_auth is None:
        raise get_unauthorized_exception('Could not validate credentials')
    await update_last_visit(user_auth.id)
    return user_auth


@auth_router.post('/token/', response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_auth: UserAuth = await authenticate_user(form_data.username, form_data.password)
    if not user_auth:
        raise get_unauthorized_exception('Incorrect username or password')
    await update_last_login(user_auth.id)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user_auth.username}, expires_delta=access_token_expires
    )
    return {'access_token': access_token, 'token_type': 'bearer'}
