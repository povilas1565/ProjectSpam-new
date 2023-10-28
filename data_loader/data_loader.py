class DataLoader:
    def __init__(self, base_path) -> None:
        self._base_path = base_path

    def load_data(self, end_file):
        with open(f'{self._base_path}/{end_file}', 'r', encoding='utf-8') as file:
            return [line for line in file.readlines() if len(line) > 5]
