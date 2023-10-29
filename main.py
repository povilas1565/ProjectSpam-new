from account_actions.account_loader import AccountsLoader
from account_actions.telethon_account import TelethonAccount
import asyncio

account_path = "E:/accounts/1/"  # папка с аккаунтами


async def onload(path, client):
    print(f"loaded", path)


async def onerror(path, error):
    print(f"error", error)

text = """Сдаётся в долгосрочную аренду квартира в Аликанте.
Одна спальня и салон с выходом на балкон .
Новый ремонт, Новые техника и мебель . Никто не жил  
Первый этаж без лифта .
Хороший район Флорида.
Пешая доступность к деловому центру .
Квартира сдаётся на год с продлением и пропиской .
Стоимость аренды 700 евро в месяц плюс коммунальные .
Доп информация и фото по
WhatsApp +34 641428185"""

async def main():
    loader = AccountsLoader(limit=asyncio.Semaphore(1))

    client = await loader.login_to_account(account_path)

    tclient = TelethonAccount(asyncio.Semaphore(1), client)

    await tclient.run_task(tclient.follow_to("https://t.me/spainrent"))

    await asyncio.sleep(2)

    await tclient.run_task(tclient.send_message_to("https://t.me/spainrent", text))

asyncio.run(main())