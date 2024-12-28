from fastapi import APIRouter, Response
from datetime import timedelta, datetime
import jwt

# Create APIRouter instance
router = APIRouter()

# JWT Configuration (simplified)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Auto-login middleware that can be used by the main app
async def auto_login_middleware(request, call_next):
    response = await call_next(request)

    # If there's no access token cookie, add it
    if not request.cookies.get("access_token"):
        access_token = create_access_token(data={"sub": "user"})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax"
        )

    return response