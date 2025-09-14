from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import calendar



MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март",
    4: "Апрель", 5: "Май", 6: "Июнь",
    7: "Июль", 8: "Август", 9: "Сентябрь",
    10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

def get_calendar(year: int, month: int, call_day: str, name):
    month_calendar = calendar.monthcalendar(year, month)

    # заголовок дней недели
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    keyboard: list[list[InlineKeyboardButton]] = [[
        InlineKeyboardButton(text=day, callback_data="ignore") for day in days
    ]]

    # числа месяца
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                row.append(InlineKeyboardButton(
                    text=str(day),
                    callback_data=f"{call_day}:{day}:{month}:{year}"
                ))
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(text="<<", callback_data=f"{name}prev:{month}:{year}"),
        InlineKeyboardButton(text=MONTHS[month], callback_data="ignore"),
        InlineKeyboardButton(text=">>", callback_data=f"{name}next:{month}:{year}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)