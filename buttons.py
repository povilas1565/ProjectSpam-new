from aiogram import Bot, Dispatcher, types, F

class Menu:
    main_menu = [
        [
            types.KeyboardButton(text="Добавить объявление"),
            types.KeyboardButton(text="Статус объявлений"),
            types.KeyboardButton(text="Удалить объявление"),
        ],
        [
            types.KeyboardButton(text="Обновить список ссылок"),
            types.KeyboardButton(text="Настроить N время"),
            types.KeyboardButton(text="Пауза объявления"),
        ],
        [
            
            types.KeyboardButton(text="Добавить аккаунты"),
            types.KeyboardButton(text="Статус аккаунтов"),
            types.KeyboardButton(text="Обновить список аккаунтов"),
        ],
    ]

class Common:
    cancel = [
        [
            types.KeyboardButton(text="Отмена"),
        ],
    ]

    complete = [
        [
            types.KeyboardButton(text="Готово"),
            types.KeyboardButton(text="Отмена"),
        ],
    ]

    yes_or_not = [
        [
            types.KeyboardButton(text="Да"),
            types.KeyboardButton(text="Отмена"),
        ],
    ]