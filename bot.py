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
from archive_manager import ArchiveManager
import common_tools

bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

adv_manager = AdvertisementManager()

distributor = AdvDistributor()


@dp.message(F.text.lower() == "отмена")
async def cancel(message: types.Message, state: FSMContext):
    await message.answer(f"Действие отменено")
    return await command_start(message, state)


@dp.message(F.text.lower() == "статус объявлений")
async def ad_remove(message: types.Message, state: FSMContext):
    links = common_tools.read_file(settings.LINKS_PATH)

    if len(links) > 0:

        text = f""

        for key, value in distributor.run_items_info.items():
            text += f"📣 {key}. Название объявления: {value.adv_item.name} | Статус: {value.status}\n"

        if len(text) > 1:
            await message.answer(text)
        else:
            await message.answer(f"📣 В работе объявлений нет")
    else:
        await message.answer(f"❌ Ошибка: список ссылок не загружен. Не можем запустить объявления в работу")

    return await command_start(message, state)


@dp.message(F.text.lower() == "удалить объявление")
async def ad_remove(message: types.Message, state: FSMContext):
    current_list = adv_manager.get_all_advertisement()

    text = f""

    for item in current_list:
        text += f"📣 {item.id}. Название объявления: {item.name}\n"

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
        await message.answer(f"❌ В базе данных еще нет объявлений")

@dp.message(F.text.lower() == "пауза объявления")
async def ad_remove(message: types.Message, state: FSMContext):
    current_list = adv_manager.get_all_advertisement()

    text = f""

    for item in current_list:
        text += f"📣 {item.id}. Название объявления: {item.name}\n"

    if len(text) > 0:
        await message.answer(
            f"{text}\n\nСтавим объявление на паузу. Введите ID объявления для паузы",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=buttons.Common.cancel,
                resize_keyboard=True,
            )
        )
        await state.set_state(states.AdvertisManager.pause_ad)
    else:
        await message.answer(f"❌ В базе данных еще нет объявлений")

@dp.message(states.AdvertisManager.pause_ad)
async def get_adv_id_delete(message: types.Message, state: FSMContext):
    adv_id = message.text

    res = adv_manager.pause_unpause_ad(adv_id)

    if res is not None:
        try:
            if not res.is_paused:
                await distributor.on_ad_removed(adv_id)
                await message.answer(f"✅ Реклама с id {adv_id} поставлена на паузу")
            else:
                await distributor.on_ad_added(res)
                await message.answer(f"✅ Реклама с id {adv_id} снята с паузы и добавлена на публикацию")
        except Exception as e:
            await message.answer(f"❌ Ошибка постановки объявления на паузу: {e}")
    else:
        await message.answer("❌ Не смогли поставить объявление на паузу. Смотрите логи")

    return await command_start(message, state)


@dp.message(states.AdvertisManager.delete_ad)
async def get_adv_id_delete(message: types.Message, state: FSMContext):
    adv_id = message.text

    if adv_manager.remove_ad(adv_id):
        try:
            await distributor.on_ad_removed(adv_id)
            await message.answer(f"✅ Реклама с id {adv_id} успешно удалена")
        except Exception as e:
            await message.answer(f"❌ Ошибка удаления объявления: {e}")
    else:
        await message.answer("❌ Не смогли удалить рекламу. Смотрите логи")

    return await command_start(message, state)


@dp.message(F.text.lower() == "добавить аккаунты")
async def get_ad_name(message: types.Message, state: FSMContext):
    await message.answer(
        "🚀 Хорошо, добавляем аккаунт(ы) к уже существующим. Вставьте ссылку на яндекс диск с zip архивом аккаунта(ов)",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        )
    )
    await state.set_state(states.AccountUpload.waiting_file)


@dp.message(states.AccountUpload.waiting_file)
async def get_zip_links(message: types.Message, state: FSMContext):

    Path(f"{settings.ACCOUNTS_PATH}/ready").mkdir(parents=True, exist_ok=True)

    await message.answer("🚀 Скачиваем аккаунты....")

    if await YandexDiskManager.download_file(message.text, f"{settings.ACCOUNTS_PATH}/tmp.zip"):

        await message.answer("💯 Аккаунты загружены. Распаковываем...")

        try:
            folders = ArchiveManager.unzip(f"{settings.ACCOUNTS_PATH}/tmp.zip", f"{settings.ACCOUNTS_PATH}/ready/")
            await message.answer(
                f"📊 Текущее количество аккаунтов: {len(next(os.walk(f'{settings.ACCOUNTS_PATH}/ready/'))[1])}\n\nПодгружаем аккаунты...")

            result_folders = []

            for folder in folders:
                result_folders.append(f'{settings.ACCOUNTS_PATH}/ready/{folder}')

            results = await distributor.store.add_account(result_folders)

            for result in results:
                if result.error is not None:
                    await message.answer(f"❌ Ошибка подгрузки аккаунта {result.account_path}: {result.error}")

            await message.answer(
                f"🎉 Текущее количество аккаунтов в работе: {await distributor.store.get_accounts_count()}")

        except Exception as e:
            await message.answer(f"❌ Не можем распаковать архив: {e}")

        return await command_start(message, state)

    else:
        await message.answer("❌ Не удалось скачать аккаунты. Проверьте ссылку и попробуйте еще раз",
                             reply_markup=types.ReplyKeyboardMarkup(
                                 keyboard=buttons.Common.cancel,
                                 resize_keyboard=True,
                             ))


@dp.message(F.text.lower() == "обновить список аккаунтов")
async def get_ad_name(message: types.Message, state: FSMContext):
    await message.answer(
        "🚀 Хорошо, полностью заменяем существующие аккаунты на новые. Загрузите архив в zip архиве",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        )
    )
    await state.set_state(states.AccountsReplace.waiting_file)


@dp.message(F.text.lower() == "статус аккаунтов")
async def get_ad_name(message: types.Message, state: FSMContext):
    count = await distributor.store.get_accounts_count()
    await message.answer(f"🎉 Количество аккаунтов в работе: {count}")
    return await command_start(message, state)


@dp.message(states.AccountsReplace.waiting_file)
async def get_zip_links(message: types.Message, state: FSMContext):
    Path(f"{settings.ACCOUNTS_PATH}/ready").mkdir(parents=True, exist_ok=True)

    await message.answer("🧹 Очищаем текущие аккаунты...")

    await distributor.store.unload_accounts()

    try:
        shutil.rmtree(f'{settings.ACCOUNTS_PATH}/ready')
    except Exception as e:
        logger.warning(f"Cannot clear accounts folder: {e}")

    await message.answer("🚀 Скачиваем аккаунты....")

    if await YandexDiskManager.download_file(message.text, f"{settings.ACCOUNTS_PATH}/tmp.zip"):

        try:
            folders = ArchiveManager.unzip(f"{settings.ACCOUNTS_PATH}/tmp.zip", f"{settings.ACCOUNTS_PATH}/ready/")

            await message.answer(
                f"🎉 Текущее количество аккаунтов: {len(next(os.walk(f'{settings.ACCOUNTS_PATH}/ready/'))[1])}\n\nПодгружаем аккаунты...")

            result_folders = []

            for folder in folders:
                result_folders.append(f'{settings.ACCOUNTS_PATH}/ready/{folder}')

            results = await distributor.store.add_account(result_folders)

            for result in results:
                if result.error is not None:
                    await message.answer(f"❌ Ошибка подгрузки аккаунта {result.account_path}: {result.error}")
            await message.answer(
                f"🎉 Текущее количество аккаунтов в работе: {await distributor.store.get_accounts_count()}")

        except Exception as e:
            await message.answer(f"❌ Не можем распаковать архив: {e}")

        return await command_start(message, state)

    else:
        await message.answer("❌ Не удалось скачать аккаунты. Проверьте ссылку и попробуйте еще раз",
                             reply_markup=types.ReplyKeyboardMarkup(
                                 keyboard=buttons.Common.cancel,
                                 resize_keyboard=True,
                             ))


@dp.message(F.text.lower() == "добавить объявление")
async def get_ad_name(message: types.Message, state: FSMContext):
    account_count = await distributor.store.get_accounts_count()
    ad_count = len(adv_manager.get_all_advertisement())

    if account_count > ad_count:
        await message.answer(
            "🚀 Хорошо, добавляем объявление. Введите короткое название для объявления (для удобства, далее будет использовано)",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=buttons.Common.cancel,
                resize_keyboard=True,
            )
        )
        await state.set_state(states.NewAdv.name)
    else:
        await message.answer(
            f"❌ Не можем добавить объявление. Текущее количество аккаунтов {account_count}, количество объявлений: {ad_count}\n\nЗагрузите больше акаунтов и повторите попытку")
        return await command_start(message, state)


@dp.message(F.text.lower() == "обновить список ссылок")
async def upload_links(message: types.Message, state: FSMContext):
    await message.answer(
        "🚀 Хорошо, обновляем список ссылок. Загрузите txt со списоком групп (каждая группа с новой строки)",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        )
    )
    await state.set_state(states.LinksUpload.waiting_file)


@dp.message(states.LinksUpload.waiting_file, F.content_type.in_({"document"}))
async def get_links(message: types.Message, state: FSMContext):

    Path(f"/var/lib/tgspam/data/common").mkdir(parents=True, exist_ok=True)
    
    if message.document is not None:
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        await bot.download_file(file_path, settings.LINKS_PATH)
        await message.answer("✅ Список ссылок обновлен!")
        return await command_start(message, state)
    else:
        await message.answer("❌ Документ не прикреплен", reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        ))


@dp.message(states.NewAdv.name)
async def get_ad_text(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    await message.answer(
        f"🚀 Хорошо, название объявления будет: {message.text}\n\n Введите текст объявления",
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
        f"🚀 Хорошо, текст объявления будет: {message.text}\n\n Теперь выберите час публикации. К примеру: 12\nЕсли объявление будет публиковаться каждые N минут - напишите -1",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons.Common.cancel,
            resize_keyboard=True,
        )
    )

    await state.set_state(states.NewAdv.publish_time)

@dp.message(states.NewAdv.publish_time)
async def get_ad_text(message: types.Message, state: FSMContext):

    try:
        ad_time = int(message.text)
        if ad_time == -1:
            await message.answer("Хорошо, объявление будет публиковаться каждые N минут\n\nТеперь добавьте картинки, а когда закончите - нажмите кнопку готово")
            await state.update_data(publish_time=None)
            await state.set_state(states.NewAdv.photos)
        else:
            await state.update_data(publish_time=ad_time)
            await message.answer(
                f"🚀 Хорошо, объявление будет публиковаться каждый день в {message.text} часа(ов). \n\n Теперь добавьте картинки, а когда закончите - нажмите кнопку готово",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=buttons.Common.cancel,
                    resize_keyboard=True,
                )
            )
            await state.set_state(states.NewAdv.photos)
    except Exception as e:
        await message.answer(f"❌ Ошибка валидации времени публикации: {e}\n\nВозможно указано не число. Попробуйте еще раз")


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
            f"✅ Фотография добавлена",
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

    await message.answer(f"💬 Текст объявления будет:\n\n{current_data['text']}")

    await message.answer(
        f"🤔 Все верно?",
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
                f"🚀 Скачиваем изображения...")
            for i, img in enumerate(current_data.get("photos")):
                filename = str(uuid.uuid4())
                Path(f"{settings.PHOTOS_PATH}/{current_data['name']}/").mkdir(parents=True, exist_ok=True)
                await bot.download_file(img['file_path'],
                                        f"{settings.PHOTOS_PATH}/{current_data['name']}/{filename}.jpg")

                images_paths.append(f"{settings.PHOTOS_PATH}/{current_data['name']}/{filename}.jpg")

    result = adv_manager.create_advertisement(current_data['name'],
                                              current_data['text'],
                                              images_paths,
                                              current_data['publish_time'])

    if result.status == AdvertisementCreateStatus.ALREADY_EXIST:
        await message.answer(
            f"❌ Объявление с названием {current_data['name']} уже существует в базе данных. Назовите как-нибудь по-другому")
    if result.status == AdvertisementCreateStatus.FAILED:
        await message.answer(f"❌ Во время сохранени объявления произошла ошибка. Попробуйте еще раз")
    else:

        await message.answer(
            f"✅ Готово. Объявление добавлено в обработку. ID объявления: {result.item.id}")

        await distributor.on_ad_added(result.item)

    return await command_start(message, state)


@dp.message(Command("start"))
async def command_start(message: types.Message, state: FSMContext) -> None:
    if message.from_user.id in settings.ALLOWED_CHATS:
        await state.clear()
        await state.set_state(states.MainMenu.menu)
        await message.answer(
            "🚀 Что хотите сделать?",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=buttons.Menu.main_menu,
                resize_keyboard=True,
            )
        )
    else:
        await message.answer(f"Ошибка: у вас нет доступа к боту")


async def main():

    res = common_tools.get_files_in_dir(f'{settings.ACCOUNTS_PATH}/ready')

    await distributor.store.add_account(res)

    results = adv_manager.get_all_advertisement()

    for res in results:
        await distributor.on_ad_added(res)

    asyncio.create_task(distributor.run())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
