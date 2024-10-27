
# Импорт библиотек
import os
import pandas as pd

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


def update_csv_from_log(csv_file, log_file):
    """Функция для обновления CSV на основе логов переименования."""
    
    # Чтение данных из CSV
    df = pd.read_csv(csv_file)

    # Чтение логов и обновление путей в DataFrame
    with open(log_file, "r") as log:
        for line in log:
            old_path, new_path = line.strip().split(',')
            # Обновление пути в столбце 'local_path'
            df.loc[df['local_path'] == old_path, 'local_path'] = new_path

    # Сохранение изменений в CSV
    df.to_csv(csv_file, index=False)
    print(f"CSV файл '{csv_file}' обновлен на основе логов.")


def undo_rename(log_file_path):
    log_file = log_file_path
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
    log_file_path = os.path.join(directory_path, "WB-ML-Photo-Classification/renaming_log.txt")
    csv_file_path = 'D:/Projects/Curent Projects/WB-ML-Photo-Classification/feedback_images.csv'
    
    # Переименовываем файлы и создаем лог
    rename_photos(directory_path)
    
    # Обновляем CSV файл на основе логов
    update_csv_from_log(csv_file_path, log_file_path)

    # Отмена переименования
    # undo_rename(directory_path)
