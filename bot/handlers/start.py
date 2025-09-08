from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from bot.keyboards.user_kb import StaticKb
from bot.style.html_message import html_message_contact, html_start_command



router = Router()


@router.message(Command("start"))
async def start_command(message: Message):
    photo = FSInputFile("bot/handlers/bot_welcome.png")
    await message.answer_photo(
        photo=photo,
        caption=html_start_command,
        parse_mode="HTML",
        reply_markup=StaticKb.start_reply
    )


@router.message(F.text=='Контакты')
async def send_contact(message: Message):
    await message.answer_location(latitude='55.677925', longitude='37.281180')
    await message.answer(text=html_message_contact, parse_mode='HTML')