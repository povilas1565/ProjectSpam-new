import zipfile
import settings

with zipfile.ZipFile(f"{settings.ACCOUNTS_PATH}/tmp.zip", 'r') as zip_ref:
    print(zip_ref.extractall(f"{settings.ACCOUNTS_PATH}/ready/"))