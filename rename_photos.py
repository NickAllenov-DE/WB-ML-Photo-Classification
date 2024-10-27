
# Импорт библиотек
import os

def rename_photos(directory):
    
    files = os.listdir(directory)   # Получаем список всех файлов в указанной директории
    id_counter = 1          # Начальный счетчик для уникальных ID
    log_file = os.path.join(directory, "renaming_log.txt")  # Файл для записи логов переименования (на случай восстановления имен)

    with open(log_file, "w") as log:
        for filename in files:
            # Проверяем, является ли файл изображением
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                # Форматируем новое имя файла с уникальным ID
                new_name = f"{id_counter:05}.jpg"  # Формат с ведущими нулями
                # Полные пути к старому и новому файлам
                old_file = os.path.join(directory, filename)
                new_file = os.path.join(directory, new_name)

                # Пишем старое и новое имя в лог
                log.write(f"{old_file},{new_file}\n")

                # Переименовываем файл
                os.rename(old_file, new_file)
                print(f"Переименован: {old_file} -> {new_file}")

                id_counter += 1  # Увеличиваем счетчик


def undo_rename(directory):
    log_file = os.path.join(directory, "renaming_log.txt")
    if not os.path.exists(log_file):
        print("Лог-файл не найден, отмена невозможна.")
        return

    # Чтение лога и переименование файлов обратно
    with open(log_file, "r") as log:
        lines = log.readlines()
        for line in reversed(lines):
            old_file, new_file = line.strip().split(',')
            if os.path.exists(new_file):
                os.rename(new_file, old_file)
                print(f"Возвращено: {new_file} -> {old_file}")



if __name__ == '__main__':
    directory_path = 'D:/Projects/Curent Projects/wb-diapers-photos'
    
    # Переименование файлов
    rename_photos(directory_path)

    # Отмена переименования
    # undo_rename(directory_path)
