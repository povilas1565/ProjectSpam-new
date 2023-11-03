from aiogram.fsm.state import State, StatesGroup

class NewAdv(StatesGroup):
    name = State()
    text = State()
    publish_time = State()
    photos = State()
    check = State()

class MainMenu(StatesGroup):
    menu = State()

class LinksUpload(StatesGroup):
    waiting_file = State()

class AccountUpload(StatesGroup):
    waiting_file = State()

class AccountsReplace(StatesGroup):
    waiting_file = State()

class AdvertisManager(StatesGroup):
    delete_ad = State()
    pause_ad = State()
