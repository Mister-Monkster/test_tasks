import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums import ParseMode
import asyncio
import os
from dotenv import load_dotenv
from backend import check_token, check_imei_api, get_whitelist, get_token, add_user
from models import GetUserModel
from schemas import TokenSchema, IMEISchema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(os.name)

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

IMEI_CHECK_URL = os.getenv("IMEI_URL")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(parse_mode=ParseMode.HTML)


@dp.message(Command('start'))
async def start(message: Message):
    user_id = message.from_user.id
    whitelist = await get_whitelist(user_id)
    if not whitelist:
        await bot.send_message(message.chat.id, "Вы не в белом списке. Доступ запрещен")
    else:
        await bot.send_message(message.chat.id, "Доступ разрешен")


@dp.message(Command('token'))
async def token_info(message: Message):
    user_id = message.from_user.id
    whitelist = await get_whitelist(user_id)
    if not whitelist:
        return None
    data = message.text.split('/token ')[1]
    req = await check_token(user_id, TokenSchema(token=data))
    if req['status_code'] == 201:
        return await bot.send_message(message.chat.id, 'Ваш токен успешно привязан к вашему id')
    else:
        return await bot.send_message(message.chat.id, "Ваш токен невалидный")


@dp.message(Command('imei'))
async def imei_info(message: Message):
    user_id = message.from_user.id
    whitelist = await get_whitelist(user_id)
    if not whitelist:
        return None
    token = await get_token(user_id)
    if token != None:
        data = message.text.split('/imei ')[1]
        req = check_imei_api(IMEISchema(imei=data, user=user_id, token=token[0]))
        if req:
            return await bot.send_message(message.chat.id,
                                          f'Вот информация по вашему IMEI:\n<code>{req['data']}</code>',
                                          parse_mode=ParseMode.HTML)


@dp.message(Command('adduser'))
async def add(message: Message):
    user_id = message.from_user.id
    whitelist = await get_whitelist(user_id)
    if not whitelist:
        return None
    data = message.text.split('/adduser')[1]
    print(int(data))
    await add_user(user_id=int(data))
    return await bot.send_message(message.chat.id, 'Пользователь успешно добавлен в белый список!')


async def run_bot():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
