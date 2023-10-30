def get_free_account():
    for key, value in free.items():
        if value is False:
            return key
    return None

test = [51, 52, 53]

free = {}

def on_added():
    for t in test:
        if t not in free:
            free[t] = False

on_added()

print(free.items())

# Пример использования функции get_free_account():
free_key = get_free_account()
if free_key is not None:
    print(f"Свободный аккаунт: {free_key}")
else:
    print("Нет свободных аккаунтов")