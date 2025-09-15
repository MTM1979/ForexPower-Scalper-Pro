from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jwt
import os

router = APIRouter()
SECRET_KEY = os.getenv("JWT_SECRET", "forexsecret")

class LoginPayload(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(payload: LoginPayload):
    # Replace with real user validation
    if payload.username == "admin" and payload.password == "scalp123":
        token = jwt.encode({"sub": payload.username}, SECRET_KEY, algorithm="HS256")
        return {"token": token}
    raise HTTPException(status_code=401, detail="Invalid credentials")
