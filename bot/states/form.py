from aiogram.fsm.state import State, StatesGroup


class DataConsultation(StatesGroup):
    name_user = State()
    name_business = State()
    experience_ad = State()
    date = State()
    time = State()


class AddTime(StatesGroup):
    time = State()
    quantity = State()
    hours_input = State()


class DeleteTime(StatesGroup):
    time = State()


