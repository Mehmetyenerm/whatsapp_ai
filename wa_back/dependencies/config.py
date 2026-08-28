from fastapi import Header, HTTPException
from secrets import compare_digest
from dependencies.settings import get_settings

def verify_api_key(x_api_key: str = Header(...)):
    expected = get_settings().webhook_api_key
    if not compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )
    return {"message": "ok"}