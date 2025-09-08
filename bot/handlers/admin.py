import datetime
import os
import asyncio
import re
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, CallbackQuery
from bot.keyboards.calender import get_calendar
from bot.keyboards.admin_kb import StaticKbAdmin, SqlTimeAdminKb
from bot.keyboards.user_kb import StaticKb
from bot.keyboards.admin_kb import AdminKbStatus, ExitButton
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
    kb = get_calendar(today.year, today.month)
    await message.answer(text='Напишите какое свободное\nвремя вы хотите добавить?\n'
                         '(в формате 00:00)',
                         reply_markup=kb)


@admin_router.callback_query(F.data.startswith("day"))
async def process_day(callback: CallbackQuery, state: FSMContext):
    _, day, month, year = callback.data.split(":")
    date = f"{day}-{month}-{year}"
    await callback.message.answer(f"Ты выбрал дату: {date}")
    await callback.answer()
    await state.update_data(time=date)


@admin_router.callback_query(F.data.startswith("prev"))
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


@admin_router.callback_query(F.data.startswith("next"))
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


#@admin_router.message(AddTime.time)
#async def request_data_add_time(message: Message, state: FSMContext):
#    if message.text == 'Выйти':
#
#        await state.clear()
#        await admin_handler(message,
#                            text="Выберите действие, которое хотите сделать",
#                            kb=StaticKbAdmin.admins_commands)
#
#    elif bool(re.fullmatch(r"(?:[0-9]|[01]\d|2[0-3]):[0-5]\d", message.text)):
#
#        await state.update_data(time=message.text)
#        data = await state.get_data()
#        try:
#            add_time(data['time'])
#            await message.answer(text='Время успешно добавлено ✅', reply_markup=StaticKbAdmin.admins_commands)
#            await state.clear()
#        except:
#            await message.answer(text='Извините, но это время уже существует')
#
#   else:
#        await message.answer(text='Введите корректную форму времени')

#Связанные хендлеры delete_time_handler и process_delete_time для удаления времени
@admin_router.message(F.text == '❌Удалить опр.время🕰️')
async def delete_time_handler(message: Message, state: FSMContext):
    await state.set_state(DeleteTime.time)
    await message.answer(
        text=(
            "Выберите время, которое вы хотите удалить из базы данных\n\n"
            "⚠️ Учтите! Если удалить занятое время клиента до его посещения, "
            "это может привести к неразберихе!"
        ),
        reply_markup=await SqlTimeAdminKb().choose_time()
    )


@admin_router.callback_query(F.data.startswith('delete:'))
async def process_delete_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    time_value = callback.data.split(':', 1)[1]
    delete_time_from_db(time_value)
    await state.clear()
    await callback.message.edit_text(f"Время {time_value} успешно удалено ✅")


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

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
                            f"🕐 Создан: {datetime.now().strftime('%d.%m.%Y в %H:%M')}"
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

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"time_tables_{timestamp}.xlsx"
        excel_path = os.path.join(SERVICES_DIR, excel_filename)

        success = sqlite_to_excel_pandas(excel_path, 'time')

        if success:
            await processing_msg.delete()

            if os.path.exists(excel_path):
                excel_file = FSInputFile(excel_path)
                await message.answer_document(
                    document=excel_file,
                    caption=f"📊 Excel файл с данными по времени\n"
                            f"🕐 Создан: {datetime.now().strftime('%d.%m.%Y в %H:%M')}"
                )
                os.remove(excel_path)
            else:
                await message.answer("❌ Файл не был создан")
        else:
            await processing_msg.edit_text("❌ Ошибка при создании Excel файла")

    except Exception as e:
        print(f"Ошибка при создании Excel файла: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
