from email import message_from_string

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, CallbackQuery


router = Router()


@router.message(Command('info'))
async def info_command(message: Message):
    await message.answer(text='Информация о записи\n'
                         'Ваше имя\n'
                         'Ваш бизнес\n'
                         'Время записи\n'
                         'День записи')