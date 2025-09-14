from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.db import request_all_db_t


class StaticKb:
    start_reply = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Запись'), KeyboardButton(text='Контакты')]
        ], resize_keyboard=True, one_time_keyboard=True
    )

    choose_anwser = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да',
                                  callback_data='+')],
            [InlineKeyboardButton(text='Нет',
                                  callback_data='-')],
            [InlineKeyboardButton(text='Пробовал сам',
                                  callback_data='own_exp')]
        ]
    )

class SqlKb:
    async def choose_time(self, date):
        result = request_all_db_t(date)

        if not result:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Свободного времени нет ❌", callback_data="no_free_time"))
            return builder.as_markup()

        builder = InlineKeyboardBuilder()

        for (time,) in result:
            builder.add(InlineKeyboardButton(text=time, callback_data=f"time:{time}"))

        if not builder.buttons:
            builder.add(InlineKeyboardButton(text="Свободного времени нет ❌", callback_data="no_free_time"))

        return builder.adjust(3).as_markup()
