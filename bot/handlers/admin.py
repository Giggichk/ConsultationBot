import datetime
import os
import asyncio
import re


from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, CallbackQuery


from bot.keyboards.calender import get_calendar
from bot.keyboards.admin_kb import StaticKbAdmin, SqlTimeAdminKb, HoursKb
from bot.keyboards.user_kb import StaticKb
from bot.keyboards.admin_kb import AdminKbStatus
from bot.states.form import AddTime, DeleteTime
from bot.states.bot_state import bot_state
from database.db import add_time, sqlite_to_excel_pandas, delete_time_from_db, clear_all_tables
from bot.config import ADMIN_ID


admin_router = Router()
admin_router.message.filter(F.from_user.id == ADMIN_ID)


@admin_router.message(Command('admin'))
async def admin_handler(message: Message, text="✅ Доступ выполнен.\n"
                         "Выберите действие, которое хотите сделать", kb=StaticKbAdmin.admins_commands):
    await message.reply(text=text,
                        reply_markup=kb)


@admin_router.message(F.text == 'Перейти в режим консультации🛑')
async def start_for_admin(message: Message):
    if message.from_user.id == ADMIN_ID:
        temp_msg = await message.answer(
            '⏳ Переключаюсь в режим консультации...',
            reply_markup=ReplyKeyboardRemove()
        )
        await asyncio.sleep(0.5)

        await temp_msg.delete()

        await message.answer(
            f'Привет, {message.from_user.first_name} 👋\n\n'
            'Я помогаю бизнесам запускать эффективную\n'
            'рекламу в Google, Meta и TikTok.\n'
            'Если хочешь больше клиентов и не сливать\n'
            'бюджет — начни с бесплатной консультации.\n\n'
            '👇 Нажми кнопку ниже, чтобы выбрать удобное время:',
            reply_markup=StaticKb.start_reply
        )
    else:
        pass


@admin_router.message(F.text == 'Статусы и режимы')
async def status_n_mode(message: Message):
    await message.answer(text='Вы перешли во вкладку статусы и режимы\n'
                              'Пожалуйста выберите, что вас интересует?',
                         reply_markup=AdminKbStatus.admin_keyboard_states)


@admin_router.message(F.text == 'Остановить запись❌')
async def stop_record(message: Message):
    if bot_state.is_accepting_users:
        bot_state.is_accepting_users = False
        await message.reply(text='Запись пользователей остановлен')
    else:
        await message.reply(text='Запись уже остановлена 🛑')


@admin_router.message(F.text == 'Возобновить запись✅')
async def stop_record(message: Message):
    if not bot_state.is_accepting_users:
        bot_state.is_accepting_users = True
        await message.reply(text='Запись пользователей возобновлен')
    else:
        await message.reply(text='Запись уже восстановлена ☑️')


@admin_router.message(F.text == '🔙Назад')
async def back_message_kb(message: Message):
    await admin_handler(message,
                        text="Выберите действие, которое хотите сделать",
                        kb=StaticKbAdmin.admins_commands)


@admin_router.message(F.text == '🕗Добавить прием')
async def add_time_handler(message: Message, state: FSMContext):
    await state.set_state(AddTime.time)
    today = datetime.date.today()
    kb = get_calendar(today.year, today.month, "add_time_day", "A")
    await message.answer(text='Выберите день:',
                         reply_markup=kb)


@admin_router.callback_query(F.data.startswith("add_time_day"))
async def process_day(callback: CallbackQuery, state: FSMContext):
    _, day, month, year = callback.data.split(":")
    date = f"{day}-{month}-{year}"

    await callback.answer()
    await state.update_data(time=date)
    await state.set_state(AddTime.quantity)
    await callback.message.delete()
    await callback.message.answer(text="Сколько записей в день?",
                                  reply_markup=ReplyKeyboardRemove())


@admin_router.callback_query(F.data.startswith("Aprev"))
async def process_prev(callback: CallbackQuery):
    _, month, year = callback.data.split(":")
    month, year = int(month), int(year)

    if month == 1:
        month, year = 12, year - 1
    else:
        month -= 1

    kb = get_calendar(year, month, "add_time_day", "A")
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@admin_router.callback_query(F.data.startswith("Anext"))
async def process_next(callback: CallbackQuery):
    _, month, year = callback.data.split(":")
    month, year = int(month), int(year)

    if month == 12:
        month, year = 1, year + 1
    else:
        month += 1

    kb = get_calendar(year, month, "add_time_day", "A")
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@admin_router.message(AddTime.quantity)
async def process_add_time(message: Message, state: FSMContext):
    try:
        qty = int(message.text)
        if qty <= 0:
            await message.answer(text="Введите положительное число.")
            return
    except ValueError:
        await message.answer(text="Введите число.")
        return

    await state.update_data(quantity=qty, counter=0, hours=[])
    await state.set_state(AddTime.hours_input)

    await message.answer(text=f"🕗Введите время записи - 1:",
                         reply_markup=HoursKb.hours_kb)


@admin_router.message(AddTime.hours_input)
async def process_hours_input(message: Message, state: FSMContext):
    user_data = await state.get_data()

    qty = user_data["quantity"]
    counter = user_data["counter"]
    hours = user_data["hours"]
    date = user_data["time"]

    text = message.text.strip()

    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", text):
        await message.answer(text="⛔ Неверный формат. Введите время в формате 00:00 (например 09:30).")
        return

    if text in hours:
        await message.answer("⛔ Это время вы уже ввели.")
        return

    hours.append(text)

    counter += 1
    await state.update_data(counter=counter, hours=hours)
    if counter < qty:
        await message.answer(text=f"🕗Введите время записи - {counter + 1}:")
    else:
        await message.answer(text="✅ Все времена добавлены:",
                             reply_markup=StaticKbAdmin.admins_commands)

        for h in hours:
            await message.answer(text=f"— {h}")
            add_time(date, h)

        await state.clear()


@admin_router.message(F.text == '❌Удалить приемы')
async def delete_time_handler(message: Message, state: FSMContext):
    await state.set_state(DeleteTime.time)

    today = datetime.date.today()
    kb = get_calendar(today.year, today.month, "delete_time_day", "D")

    await message.answer(text='Выберите день:', reply_markup=kb)


@admin_router.callback_query(F.data.startswith('delete_time_day'))
async def process_delete(callback: CallbackQuery, state: FSMContext):
    _, day, month, year = callback.data.split(":")
    date = f"{day}-{month}-{year}"

    await state.update_data(day=date)
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(text=(
            "Выберите время, которое вы хотите удалить из базы данных\n\n"
            "⚠️ Учтите! Если удалить занятое время клиента до его посещения, "
            "это может привести к неразберихе!"
        ),
        reply_markup=await SqlTimeAdminKb().choose_time(date))


@admin_router.callback_query(F.data.startswith("Dprev"))
async def process_prev(callback: CallbackQuery):
    _, month, year = callback.data.split(":")
    month, year = int(month), int(year)

    if month == 1:
        month, year = 12, year - 1
    else:
        month -= 1

    kb = get_calendar(year, month, "delete_time_day", "D")
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@admin_router.callback_query(F.data.startswith("Dnext"))
async def process_next(callback: CallbackQuery):
    _, month, year = callback.data.split(":")
    month, year = int(month), int(year)

    if month == 12:
        month, year = 1, year + 1
    else:
        month += 1

    kb = get_calendar(year, month, "delete_time_day", "D")
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@admin_router.callback_query(F.data.startswith('delete:'))
async def process_delete_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    time_value = callback.data.split(':', 1)[1]
    get_date = await state.get_data()
    delete_time_from_db(time_value, get_date['day'])

    await state.clear()
    await callback.message.answer(text='Время успешно удалено')


@admin_router.callback_query(F.data == "exit")
async def process_exit(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.answer(
        "Выберите действие, которое вы хотите выбрать",
        reply_markup=StaticKbAdmin.admins_commands
    )
    await callback.message.delete()


@admin_router.callback_query(F.data == 'not_time')
async def not_process_time(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(text='Выберите действие, которое хотите сделать', reply_markup=StaticKbAdmin.admins_commands)


@admin_router.message(F.text == 'Очистить базу данных🗃️')
async def clear_db(message: Message):
    clear_all_tables()
    await message.answer('База очищена')


@admin_router.message(F.text == 'Создать Excel-файл консультаций📊')
async def create_excel_file(message: Message):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_DIR = os.path.dirname(BASE_DIR)
    SERVICES_DIR = os.path.join(PROJECT_DIR, "services")
    os.makedirs(SERVICES_DIR, exist_ok=True)

    try:
        processing_msg = await message.answer("⏳ Создаю Excel файл...")

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"consultations_{timestamp}.xlsx"
        excel_path = os.path.join(SERVICES_DIR, excel_filename)

        success = sqlite_to_excel_pandas(excel_path, 'Record')

        if success:
            await processing_msg.delete()

            if os.path.exists(excel_path):
                excel_file = FSInputFile(excel_path)
                await message.answer_document(
                    document=excel_file,
                    caption=f"📊 Excel файл с данными консультаций\n"
                            f"🕐 Создан: {datetime.datetime.now().strftime('%d.%m.%Y в %H:%M')}"
                )
                os.remove(excel_path)
            else:
                await message.answer("❌ Файл не был создан")
        else:
            await processing_msg.edit_text("❌ Ошибка при создании Excel файла")

    except Exception as e:
        print(f"Ошибка при создании Excel файла: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")


@admin_router.message(F.text == 'Создать Excel-файл времени🕰️')
async def create_excel_file_time(message: Message):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_DIR = os.path.dirname(BASE_DIR)
    SERVICES_DIR = os.path.join(PROJECT_DIR, "services")
    os.makedirs(SERVICES_DIR, exist_ok=True)

    try:
        processing_msg = await message.answer("⏳ Создаю Excel файл...")

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"time_tables_{timestamp}.xlsx"
        excel_path = os.path.join(SERVICES_DIR, excel_filename)

        success = sqlite_to_excel_pandas(excel_path, 'schedule')

        if success:
            await processing_msg.delete()

            if os.path.exists(excel_path):
                excel_file = FSInputFile(excel_path)
                await message.answer_document(
                    document=excel_file,
                    caption=f"📊 Excel файл с данными по времени\n"
                            f"🕐 Создан: {datetime.datetime.now().strftime('%d.%m.%Y в %H:%M')}"
                )
                os.remove(excel_path)
            else:
                await message.answer("❌ Файл не был создан")
        else:
            await processing_msg.edit_text("❌ Ошибка при создании Excel файла")

    except Exception as e:
        print(f"Ошибка при создании Excel файла: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
