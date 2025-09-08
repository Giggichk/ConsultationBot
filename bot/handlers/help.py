from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.keyboards.user_kb import StaticKb


router = Router()


@router.message(Command('help'))
async def help_command(message: Message):
    await message.answer('Этот бот помогает записаться на бесплатную\nконсультацию по онлайн-рекламе (Google / Meta / TikTok Ads).\n\nНажмите кнопку ниже, чтобы выбрать удобное время 👇',
                         reply_markup=StaticKb.start_reply)