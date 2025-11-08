from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import User
from ..schemas import Token, TokenRequest
from ..security import create_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: TokenRequest, db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)}, timedelta(minutes=720))
    return Token(token=token, user=user)  # type: ignore[arg-type]


@router.post("/seed", response_model=Token)
def seed_admin(db: Session = Depends(get_db)) -> Token:
    """Convenience endpoint to create a default admin during development."""
    user = db.query(User).filter(User.email == "admin@calchopper.io").first()
    if not user:
        user = User(
            workspace_id=1,
            name="Admin",
            email="admin@calchopper.io",
            password_hash=get_password_hash("admin"),
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    token = create_access_token({"sub": str(user.id)}, timedelta(minutes=720))
    return Token(token=token, user=user)  # type: ignore[arg-type]
