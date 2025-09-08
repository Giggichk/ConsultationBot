from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.db import request_all_db_t


class StaticKbAdmin:
    admins_commands = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🕗Добавить прием'), KeyboardButton(text='❌Удалить опр.время🕰️')],
            [KeyboardButton(text='Очистить базу данных🗃️')],
            [KeyboardButton(text='Статусы и режимы')],
            [KeyboardButton(text='Создать Excel-файл консультаций📊')],
            [KeyboardButton(text='Создать Excel-файл времени🕰️')]
        ],
        resize_keyboard=True
    )


class AdminKbStatus:
    admin_keyboard_states = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Возобновить запись✅'), KeyboardButton(text='Остановить запись❌')],
            [KeyboardButton(text='Статус бота🤖')],
            [KeyboardButton(text='Перейти в режим консультации🛑', )],
            [KeyboardButton(text='🔙Назад')]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


class SqlTimeAdminKb:
    async def choose_time(self):
        result = request_all_db_t()

        if not result:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="База с временем пуста!", callback_data='not_time'))
            return builder.as_markup()

        builder = InlineKeyboardBuilder()

        for (time,) in result:
            builder.add(InlineKeyboardButton(text=time, callback_data=f"delete:{time}"))

        if not builder.buttons:
            builder.add(InlineKeyboardButton(text="База с временем пуста!", callback_data="not_time"))
        else:
            builder.row(
                InlineKeyboardButton(text="❌ Выйти", callback_data="exit")
            )

        return builder.adjust(3).as_markup()


class ExitButton:
    button_ex = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Выйти')]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )