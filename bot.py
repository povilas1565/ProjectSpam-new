import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from loguru import logger
import io
from aiogram.fsm.context import FSMContext
import uuid
from pathlib import Path
import states
import buttons
import zipfile
import os
import shutil
import settings
from advertisement_manager import AdvertisementManager
from models.advertisement import AdvertisementCreateStatus
from adv_distributor import AdvDistributor
from yandex_disk_manager import YandexDiskManager

bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

adv_manager = AdvertisementManager()

async def on_loaded(path):
    print(path)

async def on_error(path, p):
    print(path)


distributor = AdvDistributor(on_loaded, on_error)

@dp.message(F.text.lower() == "отмена")
async def cancel(message: types.Message, state: FSMContext):
    await state.set_state(states.MainMenu.menu)
    await message.answer(
        "Действие отменено. Что хотите сделать?",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Menu.main_menu,
            resize_keyboard=True,
        )
    )


@dp.message(F.text.lower() == "статус объявлений")
async def ad_remove(message: types.Message, state: FSMContext):
    current_list = adv_manager.get_all_advertisement()

    text = f""

    for item in current_list:
        status = "В работе" if distributor.ad_status[item.id] else "Простаивает"
        text += f"{item.id}. Название объявления: {item.name} | Статус: {status}\n"

    if len(text) > 1:
        await message.answer(text)
    else:
        await message.answer(f"В работе объявлений нет")

    return await command_start(message, state)


@dp.message(F.text.lower() == "удалить объявление")
async def ad_remove(message: types.Message, state: FSMContext):
    current_list = adv_manager.get_all_advertisement()

    text = f""

    for item in current_list:
        text += f"{item.id}. Название объявления: {item.name}\n"

    if len(text) > 0:
        await message.answer(
            f"{text}\n\nУдаляем объявление. Введите ID объявления для удаления",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=buttons.Common.cancel,
                resize_keyboard=True,
            )
        )
        await state.set_state(states.AdvertisManager.delete_ad)
    else:
        await message.answer(f"Ошибка: в базе данных еще нет объявлений")


@dp.message(states.AdvertisManager.delete_ad)
async def get_adv_id_delete(message: types.Message, state: FSMContext):
    adv_id = message.text

    if adv_manager.remove_ad(adv_id):
        await distributor.on_ad_removed(adv_id)
        await message.answer(f"Реклама с id {adv_id} успешно удалена")
    else:
        await message.answer("Не смогли удалить рекламу. Смотрите логи")

    return await command_start(message, state)


@dp.message(F.text.lower() == "добавить аккаунты")
async def get_ad_name(message: types.Message, state: FSMContext):
    await message.answer(
        "Хорошо, добавляем аккаунт(ы) к уже существующим. Вставьте ссылку на яндекс диск с zip архивом аккаунта(ов)",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        )
    )
    await state.set_state(states.AccountUpload.waiting_file)


@dp.message(states.AccountUpload.waiting_file)
async def get_zip_links(message: types.Message, state: FSMContext):

    Path(f"{settings.ACCOUNTS_PATH}/ready").mkdir(parents=True, exist_ok=True)

    await message.answer("Скачиваем аккаунты....")

    if await YandexDiskManager.download_file(message.text, f"{settings.ACCOUNTS_PATH}/tmp.zip"):

        await message.answer("Аккаунты загружены. Распаковываем...")

        with zipfile.ZipFile(f"{settings.ACCOUNTS_PATH}/tmp.zip", 'r') as zip_ref:
            zip_ref.extractall(f"{settings.ACCOUNTS_PATH}/ready/")

        await message.answer(
            f"Текущее количество аккаунтов: {len(next(os.walk(f'{settings.ACCOUNTS_PATH}/ready/'))[1])}")

        return await command_start(message, state)
    
    else:
        await message.answer("Не удалось скачать аккаунты. Проверьте ссылку и попробуйте еще раз", reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        ))

@dp.message(F.text.lower() == "обновить список аккаунтов")
async def get_ad_name(message: types.Message, state: FSMContext):
    await message.answer(
        "Хорошо, полностью заменяем существующие аккаунты на новые. Загрузите архив в zip архиве",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        )
    )
    await state.set_state(states.AccountsReplace.waiting_file)


@dp.message(states.AccountsReplace.waiting_file)
async def get_zip_links(message: types.Message, state: FSMContext):
    Path(f"{settings.ACCOUNTS_PATH}/ready").mkdir(parents=True, exist_ok=True)

    await message.answer("Очищаем текущие аккаунты...")

    await distributor.unload_accounts()

    try:
        shutil.rmtree(f'{settings.ACCOUNTS_PATH}/ready')
    except Exception as e:
        logger.warning(f"Cannot clear accounts folder: {e}")

    await message.answer("Скачиваем аккаунты....")

    if await YandexDiskManager.download_file(message.text, f"{settings.ACCOUNTS_PATH}/tmp.zip"):

        await message.answer("Аккаунты загружены. Распаковываем...")

        with zipfile.ZipFile(f"{settings.ACCOUNTS_PATH}/tmp.zip", 'r') as zip_ref:
            zip_ref.extractall(f"{settings.ACCOUNTS_PATH}/ready/")

        await message.answer(
            f"Текущее количество аккаунтов: {len(next(os.walk(f'{settings.ACCOUNTS_PATH}/ready/'))[1])}")

        return await command_start(message, state)
    
    else:
        await message.answer("Не удалось скачать аккаунты. Проверьте ссылку и попробуйте еще раз", reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        ))

@dp.message(F.text.lower() == "добавить объявление")
async def get_ad_name(message: types.Message, state: FSMContext):
    await message.answer(
        "Хорошо, добавляем объявление. Введите короткое название для объявления (для удобства, далее будет использовано)",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        )
    )
    await state.set_state(states.NewAdv.name)


@dp.message(F.text.lower() == "обновить список ссылок")
async def upload_links(message: types.Message, state: FSMContext):
    await message.answer(
        "Хорошо, обновляем список ссылок. Загрузите txt со списоком групп (каждая группа с новой строки)",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        )
    )
    await state.set_state(states.LinksUpload.waiting_file)


@dp.message(states.LinksUpload.waiting_file, F.content_type.in_({"document"}))
async def get_links(message: types.Message, state: FSMContext):
    Path(f"./data/common/").mkdir(parents=True, exist_ok=True)
    if message.document is not None:
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        await bot.download_file(file_path, settings.LINKS_PATH)
        await message.answer("Список ссылок обновлен!")
        return await command_start(message, state)
    else:
        await message.answer("Документ не прикреплен", reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        ))


@dp.message(states.NewAdv.name)
async def get_ad_text(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    await message.answer(
        f"Хорошо, название объявления будет: {message.text}\n\n Введите текст объявления",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        )
    )

    await state.set_state(states.NewAdv.text)


@dp.message(states.NewAdv.text)
async def get_ad_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)

    await message.answer(
        f"Хорошо, текст объявления будет: {message.text}\n\n Теперь добавьте картинки, а когда закончите - нажмите кнопку готово",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        )
    )

    await state.set_state(states.NewAdv.photos)


@dp.message(states.NewAdv.photos, F.content_type.in_({"photo"}))
async def get_photo(message: types.Message, state: FSMContext):
    if message.photo is not None:

        current_data = await state.get_data()

        photo = message.photo[-1]
        file_id = photo.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path

        if current_data.get("photos") is None:
            await state.update_data(photos=[])

        photos = await state.get_data()

        photos = photos['photos']

        photos.append({"file_path": file_path, "file_id": file_id})

        await state.update_data(photos=photos)

        await message.answer(
            f"Фотография добавлена",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=buttons.Common.complete,
                resize_keyboard=True,
            )
        )


@dp.message(states.NewAdv.photos, F.text.lower() == "готово")
async def review_photo(message: types.Message, state: FSMContext):
    current_data = await state.get_data()

    images = []

    if current_data is not None:
        if current_data.get("photos") is not None:
            for i, img in enumerate(current_data.get("photos")):
                images.append(types.input_media_photo.InputMediaPhoto(media=img['file_id']))
        await message.answer_media_group(images)

    await message.answer(f"Текст объявления будет: {current_data['text']}")

    await message.answer(
        f"Все верно?",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.yes_or_not,
            resize_keyboard=True,
        )
    )
    await state.set_state(states.NewAdv.check)


@dp.message(states.NewAdv.check, F.text.lower() == "да")
async def download_photos(message: types.Message, state: FSMContext):
    current_data = await state.get_data()

    images_paths = []

    if current_data is not None:
        if current_data.get("photos") is not None:
            await message.answer(
                f"Скачиваем изображения...")
            for i, img in enumerate(current_data.get("photos")):
                filename = str(uuid.uuid4())
                Path(f"{settings.PHOTOS_PATH}/{current_data['name']}/").mkdir(parents=True, exist_ok=True)
                await bot.download_file(img['file_path'],
                                        f"{settings.PHOTOS_PATH}/{current_data['name']}/{filename}.jpg")

                images_paths.append(f"{settings.PHOTOS_PATH}/{current_data['name']}/{filename}.jpg")

    result = adv_manager.create_advertisement(current_data['name'],
                                              current_data['text'],
                                              images_paths)

    if result.status == AdvertisementCreateStatus.ALREADY_EXIST:
        await message.answer(
            f"Объявление с названием {current_data['name']} уже существует в базе данных. Назовите как-нибудь по-другому")
    if result.status == AdvertisementCreateStatus.FAILED:
        await message.answer(f"Во время сохранени объявления произошла ошибка. Попробуйте еще раз")
    else:

        await message.answer(
            f"Готово. Объявление добавлено в обработку. ID объявления: {result.item.id}")

        await distributor.on_ad_added(result.item)

    return await command_start(message, state)


@dp.message(Command("start"))
async def command_start(message: types.Message, state: FSMContext) -> None:
    await state.set_state(states.MainMenu.menu)
    await message.answer(
        "Что вы хотите сделать?",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Menu.main_menu,
            resize_keyboard=True,
        )
    )


async def main():
    await distributor.reload()

    asyncio.create_task(distributor.run())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
