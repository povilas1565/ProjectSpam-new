import zipfile

class ArchiveManager:
    @staticmethod
    def unzip(target, dist):
        folders = set()
        with zipfile.ZipFile(target, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                file_path = file_info.filename
                path_components = file_path.split('/')
                if len(path_components) > 1:
                    folders.add(path_components[0])
            zip_ref.extractall(dist)
        return folders