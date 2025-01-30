from pydantic import BaseModel


class IMEISchema(BaseModel):
    imei: str
    token: str
    user: int


class TokenSchema(BaseModel):
    token: str

