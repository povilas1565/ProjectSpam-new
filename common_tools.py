import glob
from loguru import logger
import aiohttp

def get_files_in_dir(dir):
    return glob.glob(f"{dir}/*")

def read_file(path):
    res = []
    try:
        with open(path, "r", encoding='utf-8') as file:
            for line in file.readlines():
                if len(line) > 1:
                    res.append(line)
    except Exception as e:
        logger.critical(f"Cannot load file: {e}")
    return res

def get_index_default(target: list, index: int):
    try:
        return target[index]
    except Exception as e:
        logger.warning(f"List {target=} with {index=} is empty")
        return None

async def make_get_request(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                logger.success(f"Url: {url} | {resp.status}")
    except Exception as e:
        logger.warning(e)
