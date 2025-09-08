import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states.form import DataConsultation
from bot.keyboards.user_kb import StaticKb, SqlKb
from bot.keyboards.calender import get_calendar
from database.db import update_time, add_request
from bot.Middleware.throttling import RecordMiddleware, BotStateMiddleware


router = Router()
router.message.middleware(RecordMiddleware())
router.message.middleware(BotStateMiddleware())


async def delete_and_answer(callback: CallbackQuery, text: str, reply_markup=None):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=reply_markup)


@router.message(F.text == 'Запись')
async def form_consultation(message: Message, state: FSMContext):
    await state.set_state(DataConsultation.name_user)
    await message.answer(text='👤 Ваше имя')


@router.message(DataConsultation.name_user)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name_user=message.text.strip())
    await state.set_state(DataConsultation.name_business)
    await message.answer('🗃️ Название или тематика бизнеса')


@router.message(DataConsultation.name_business)
async def process_business(message: Message, state: FSMContext):
    await state.update_data(name_business=message.text.strip())
    await state.set_state(DataConsultation.experience_ad)
    await message.answer('☑️ Есть ли у него опыт рекламы?',
                         reply_markup=StaticKb.choose_anwser)


@router.callback_query(F.data.in_(['+', '-', 'own_exp']))
async def process_exp(callback: CallbackQuery, state: FSMContext):
    await state.update_data(experience_ad=callback.data)
    await state.set_state(DataConsultation.time)
    today = datetime.date.today()
    kb = get_calendar(today.year, today.month)
    await delete_and_answer(
        callback,
        '📅 Выберите удобную дату ',
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("day"))
async def process_day(callback: CallbackQuery, state: FSMContext):
    _, day, month, year = callback.data.split(":")
    date = f"{day}-{month}-{year}"
    await callback.message.answer(f"Ты выбрал дату: {date}")
    await state.update_data(time=date)
    await callback.answer()


@router.callback_query(F.data.startswith("prev"))
async def process_prev(callback: CallbackQuery):
    _, month, year = callback.data.split(":")
    month, year = int(month), int(year)

    if month == 1:
        month, year = 12, year - 1
    else:
        month -= 1

    kb = get_calendar(year, month)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("next"))
async def process_next(callback: CallbackQuery):
    _, month, year = callback.data.split(":")
    month, year = int(month), int(year)

    if month == 12:
        month, year = 1, year + 1
    else:
        month += 1

    kb = get_calendar(year, month)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith('time:'))
async def process_time(callback: CallbackQuery, state: FSMContext):
    time_value = callback.data.split(':', 1)[1]
    update_time(time_value)

    await state.update_data(time=time_value)
    data = await state.get_data()

    if all(key in data for key in ('name_user', 'name_business', 'experience_ad', 'time')):
        add_request(
            user_id=callback.from_user.id,
            name=data['name_user'],
            business=data['name_business'],
            experience=data['experience_ad'],
            time=data['time']
        )
        await delete_and_answer(callback, "Вы успешно записаны на консультацию! ☑️")
    else:
        await delete_and_answer(callback, "Ошибка: не все данные были заполнены. Попробуйте снова.")

    await state.clear()


@router.callback_query(F.data == 'no_free_time')
async def not_process_time(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await delete_and_answer(callback, 'Пожалуйста, попробуйте подать запись в другое время')
