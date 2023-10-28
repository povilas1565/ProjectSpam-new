import glob
from loguru import logger

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
