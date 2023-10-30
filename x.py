import asyncio

async def long_run_task():
    while True:
        print("still running")
        await asyncio.sleep(1)


async def main():
    task = asyncio.ensure_future(long_run_task())

    await asyncio.sleep(3)

    task.cancel()

    print("canceled")

asyncio.run(main())

input("23")