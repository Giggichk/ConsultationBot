from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from bot.states.bot_state import bot_state
from bot.config import ADMIN_ID
from database.db import id_user_from_db


class RecordMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = getattr(getattr(event, "from_user", None), "id", None)

        # Проверка, есть ли пользователь в базе
        if user_id and id_user_from_db(user_id):
            if isinstance(event, Message) and event.text == "Запись":
                await event.answer("⛔ Вы уже записаны на консультацию.")
                return
            elif isinstance(event, CallbackQuery) and event.data == "Запись":
                await event.answer("⛔ Вы уже записаны на консультацию.", show_alert=True)
                return

        return await handler(event, data)


class BotStateMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        # Проверяем состояние бота
        if not bot_state.is_accepting_users:
            if isinstance(event, Message) and event.text == "Запись":
                await event.answer(
                    "🚫 Запись временно недоступна.\n"
                    "Попробуйте позже или свяжитесь с администратором."
                )
                return
            elif isinstance(event, CallbackQuery) and event.data == "Запись":
                await event.answer(
                    "🚫 Запись временно недоступна.\n"
                    "Попробуйте позже или свяжитесь с администратором.",
                    show_alert=True
                )
                return

        return await handler(event, data)