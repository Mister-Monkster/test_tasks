from typing import Annotated
import json
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
import requests
import logging
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy import select, text
from models import Base, UserModel, GetUserModel
from schemas import TokenSchema, IMEISchema

load_dotenv()

app = FastAPI()


async_engine = create_async_engine(
    url='sqlite+aiosqlite:///users.db',
    echo=True)

async_session_factory = async_sessionmaker(async_engine)

IMEI_CHECK_URL = os.getenv("IMEI_URL")


def check_imei(imei, token):
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'}
    body = json.dumps({
        "deviceId": imei,
        "serviceId": 12
    })

    response = requests.post(IMEI_CHECK_URL, headers=headers, data=body)
    info = response.json()
    if response.status_code == 201:
        return info
    else:
        raise HTTPException (status_code=response.status_code, detail='Error')


@app.get("/api/whitelist")
async def get_whitelist(user_id: int):
    async with async_session_factory() as session:
        query = select(GetUserModel).where(GetUserModel.id == user_id)
        res = await session.execute(statement=query)
        return res.scalars().all()


@app.get('/api/get-token')
async def get_token(user_id: int):
    async with async_session_factory() as session:
        query = select(UserModel.token).where(UserModel.id == user_id)
        res = await session.execute(statement=query)
        return res.scalars().all()


@app.post("/api/addUser")
async def add_user(user_id: int):
    new_user = GetUserModel(id=user_id)
    async with async_session_factory() as session:
        session.add(new_user)
        await session.commit()
        return {"ok": True}


@app.post("/api/check-imei")
def check_imei_api(request: IMEISchema):
    imei = request.imei
    user_id = request.user
    token = request.token
    if len(imei) != 15 or not imei.isdigit():
        return {"data": "Invalid IEMEI"}
    elif token == None:
        return {"data": "Invalid Token"}
    else:
        if token:
            return {"data": f"{check_imei(imei, token)}"}


@app.post("/api/check-token")
async def check_token(user_id: int, data: TokenSchema):
    headers = {
        'Authorization': 'Bearer ' + data.token,
        'Content-Type': 'application/json'}
    body = json.dumps({
        "deviceId": "356735111052198",
        "serviceId": 12
    })
    response = requests.post(IMEI_CHECK_URL, headers=headers, data=body)
    code = response.status_code
    if code == 201:
        async with async_session_factory() as session:
            query = text(f"UPDATE users SET token='{data.token}' WHERE id={user_id}")
            await session.execute(query)
            await session.commit()
        return {"status_code": 201}
    else:
        return {"status_code": code}


