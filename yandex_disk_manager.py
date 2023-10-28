import aiohttp
import asyncio
from urllib.parse import urlencode
from loguru import logger

class YandexDiskManager:
    @staticmethod
    async def download_file(url, output_path):
        try:
            base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
            final_url = base_url + urlencode(dict(public_key=url))

            async with aiohttp.ClientSession() as session:
                async with session.get(final_url) as response:
                    data = await response.json()
                    download_url = data['href']

                async with session.get(download_url) as download_response:
                    with open(output_path, 'wb') as f:  # Укажите нужный путь к файлу
                        while True:
                            chunk = await download_response.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
        except Exception as e:
            logger.error(e)
            return False
        
        return True