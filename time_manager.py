import aiohttp
import asyncio
from datetime import datetime
from loguru import logger

async def get_current_hour(city="Madrid"):

    url = f"http://worldtimeapi.org/api/timezone/Europe/{city}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    current_time_str = data['datetime']

                    current_time = datetime.fromisoformat(current_time_str)

                    current_hour = current_time.hour

                    return current_hour
    except Exception as e:
        logger.error(f"Не можем получить время: {e}")
    return 0
