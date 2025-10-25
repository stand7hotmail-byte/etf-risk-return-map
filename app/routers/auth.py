from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from firebase_admin import auth
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud import (
    create_user_token,
    get_password_hash,
    is_password_strong_enough,
    verify_password,
)
from app.database import get_db
from app.models import User
from app.schemas import GoogleToken, Token, UserCreate, UserInDB

router = APIRouter()

# Firebase Admin SDKの初期化 (ここで行う)
# This should be initialized once, likely in app/main.py or a dedicated config.
# For now, I will comment it out and assume it's handled elsewhere.
# cred = credentials.Certificate("etf-webapp-firebase-adminsdk-fbsvc-96649b4b25.json")
# firebase_admin.initialize_app(cred)


# ユーザー登録エンドポイント
@router.post("/register", response_model=UserInDB)
async def register_user(
    request: Request, user: UserCreate, db: Session = Depends(get_db)
) -> UserInDB:
    """Registers a new user."""
    # Rate limiting will be handled by the main app or a middleware
    # await app.state.limiter(request, "10/minute")
    if not is_password_strong_enough(user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Password is not strong enough. It must be at least 8 characters "
                "long and include at least one uppercase letter, one lowercase "
                "letter, and one number."
            ),
        )
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already registered"
        ) from None


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Authenticates a user and returns an access token."""
    # Rate limiting will be handled by the main app or a middleware
    # await app.state.limiter(request, "10/minute")
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_data = create_user_token(user.username)
    return access_token_data


@router.post("/token/google", response_model=Token)
async def login_google(
    google_token: GoogleToken, db: Session = Depends(get_db)
) -> Token:
    """Authenticates a user via Google and returns an access token."""
    try:
        # Firebase IDトークンを検証
        # Firebase Admin SDK initialization should be done once globally, not here.
        # Assuming firebase_admin is initialized in app/main.py or similar.
        decoded_token = auth.verify_id_token(google_token.token)
        email = decoded_token.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Google token.",
            )

    except auth.InvalidIdTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {e}",
        ) from e

    # データベースでユーザーを検索または作成
    user = db.query(User).filter(User.username == email).first()
    if not user:
        # ユーザーが存在しない場合は、新しいユーザーを作成
        # Googleログインユーザーはパスワードを持たないため、hashed_passwordは空にする
        new_user = User(username=email, hashed_password="")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user

    # 既存のシステムと同じように、内部用のJWTトークンを生成して返す
    access_token_data = create_user_token(user.username)
    return access_token_data
