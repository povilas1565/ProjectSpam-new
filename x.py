import zipfile
import settings

def print_folders(zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
        folder_set = set()  # Use a set to store unique folder paths
        for file_info in zip_file.infolist():
            file_path = file_info.filename
            path_components = file_path.split('/')
            if len(path_components) > 1:
                folder_set.add(path_components[0])

        for folder in folder_set:
            print(folder)

# Replace 'your_zip_file.zip' with the path to your zip file
zip_file_path = f'{settings.ACCOUNTS_PATH}/tmp.zip'
print_folders(zip_file_path)





