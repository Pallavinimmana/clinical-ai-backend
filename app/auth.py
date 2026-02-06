from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
import datetime

from .database import SessionLocal
from . import models, schemas

# ---------------- CONFIG ----------------

SECRET_KEY = "SUPER_SECRET_KEY_CHANGE_LATER"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 2

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ---------------- DATABASE ----------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- PASSWORD UTILS ----------------

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

# ---------------- JWT UTILS ----------------

def create_access_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_aud": False}
        )
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------- AUTH ROUTES ----------------

@router.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = (
        db.query(models.User)
        .filter(models.User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = models.User(
        email=user.email,
        password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully"}

@router.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    print("👉 LOGIN REQUEST RECEIVED")
    print("EMAIL FROM REQUEST:", user.email)
    print("PASSWORD FROM REQUEST:", user.password)

    db_user = (
        db.query(models.User)
        .filter(models.User.email == user.email)
        .first()
    )

    print("USER FROM DB:", db_user)

    if not db_user:
        print("❌ USER NOT FOUND IN DATABASE")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user.password, db_user.password):
        print("❌ PASSWORD DOES NOT MATCH HASH")
        print("HASH IN DB:", db_user.password)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    print("✅ LOGIN SUCCESS")

    token = create_access_token(db_user.email)

    return {
        "access_token": token,
        "token_type": "bearer"
    }
