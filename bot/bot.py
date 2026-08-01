"""
Telegram-бот первичной квалификации лидов.

Задаёт короткую последовательность вопросов (тип объекта, площадь, бюджет,
контакт) и отправляет собранные данные в бэкенд через /webhook/telegram.
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import os

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("leadflow.bot")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class Quiz(StatesGroup):
    project_type = State()
    budget = State()
    name = State()
    phone = State()


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.set_state(Quiz.project_type)
    await message.answer(
        "Здравствуйте! Помогу рассчитать стоимость проекта.\n\n"
        "Что вас интересует?\n1. Ремонт квартиры\n2. Строительство дома\n3. Коммерческий объект"
    )


@dp.message(Quiz.project_type)
async def project_type(message: Message, state: FSMContext):
    await state.update_data(project_type=message.text)
    await state.set_state(Quiz.budget)
    await message.answer("Какой бюджет вы рассматриваете (примерно, в рублях)?")


@dp.message(Quiz.budget)
async def budget(message: Message, state: FSMContext):
    await state.update_data(budget=message.text)
    await state.set_state(Quiz.name)
    await message.answer("Как к вам обращаться?")


@dp.message(Quiz.name)
async def name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Quiz.phone)
    await message.answer("Оставьте номер телефона для связи с менеджером")


@dp.message(Quiz.phone)
async def phone(message: Message, state: FSMContext):
    data = await state.get_data()
    lead = {
        "name": data["name"],
        "phone": message.text,
        "source": "telegram_bot",
        "project_type": data["project_type"],
        "budget": data["budget"],
        "utm_source": "telegram",
        "utm_medium": "bot",
    }

    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{BACKEND_URL}/webhook/telegram", json=lead, timeout=10)
        except httpx.HTTPError:
            logger.exception("Не удалось отправить лид на бэкенд")

    await message.answer("Спасибо! Наш менеджер свяжется с вами в ближайшее время.")
    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
