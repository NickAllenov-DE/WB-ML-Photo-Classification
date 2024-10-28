
# Импорт библиотек
import os
import pandas as pd


def rename_photos(directory, log_file_path):
    """Функция для переименования фотографий и создания лога."""
    
    files = os.listdir(directory)       # Получаем список всех файлов в указанной директории
    id_counter = 1      # Начальный счетчик для уникальных ID

    with open(log_file_path, "w") as log:
        for filename in files:
            # Проверяем, является ли файл изображением
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                # Форматируем новое имя файла с уникальным ID
                new_name = f"{id_counter:05}.jpg"   # Формат с ведущими нулями
                # Полные пути к старому и новому файлам
                old_file = os.path.normpath(os.path.join(directory, filename))  # Приведение к нормальному виду
                new_file = os.path.normpath(os.path.join(directory, new_name))  # Приведение к нормальному виду
                
                # Пишем старое и новое имя в лог
                log.write(f"{old_file},{new_file}\n")
                
                # Переименовываем файл
                os.rename(old_file, new_file)
                print(f"Переименован: {old_file} -> {new_file}")

                id_counter += 1 # Увеличиваем счетчик


def update_csv_from_log(csv_file, log_file_path):
    """Функция для обновления CSV на основе логов переименования с учетом регистра."""

    # Чтение данных из CSV с указанием разделителя
    df = pd.read_csv(csv_file)  # Используем `sep=';'` для правильного разделения колонок при необходимости

    # Проверка на наличие нужного столбца
    if 'local_path' not in df.columns:
        print("Ошибка: Столбец 'local_path' не найден в CSV-файле.")
        return

    # Приведение всех путей в столбце 'local_path' к нормализованному виду и нижнему регистру
    df['local_path'] = df['local_path'].apply(lambda x: os.path.normpath(x).lower())

    # Чтение логов и обновление путей в DataFrame
    with open(log_file_path, "r") as log:
        for line in log:
            old_path, new_path = line.strip().split(',')

            # Приведение путей к нормализованному виду и нижнему регистру
            old_path = os.path.normpath(old_path).lower()
            new_path = os.path.normpath(new_path).lower()

            print(f"Обновление пути: {old_path} -> {new_path}")  # Выводим информацию о обновлении
            
            # Обновление пути в столбце 'local_path'
            if old_path in df['local_path'].values:
                df.loc[df['local_path'] == old_path, 'local_path'] = new_path
            else:
                print(f"Предупреждение: старый путь '{old_path}' не найден в CSV.")  # Предупреждение, если старый путь не найден

    # Сохранение изменений в CSV
    df.to_csv(csv_file, index=False)
    print(f"CSV файл '{csv_file}' обновлен на основе логов.")





def undo_rename(log_file_path):
    """Функция для отмены переименования на основе логов."""
    
    # Проверка существования файла с логами
    if not os.path.exists(log_file_path):
        print("Лог-файл не найден, отмена невозможна.")
        return

    # Чтение лога и переименование файлов обратно
    with open(log_file_path, "r") as log:
        lines = log.readlines()
        for line in reversed(lines):
            old_file, new_file = line.strip().split(',')
            if os.path.exists(new_file):
                os.rename(new_file, old_file)
                print(f"Возвращено: {new_file} -> {old_file}")



if __name__ == '__main__':
    directory_path = 'D:/Projects/CurrentProjects/WB-ML-Photo-Classification/wb-diapers-photos'
    csv_file_path = 'D:/Projects/CurrentProjects/WB-ML-Photo-Classification/feedback_images.csv'
    log_file_path = 'D:/Projects/CurrentProjects/WB-ML-Photo-Classification/renaming_log.txt'
    
    # Переименовываем файлы и создаем лог
    rename_photos(directory_path, log_file_path)
    
    # Обновляем CSV файл на основе логов
    update_csv_from_log(csv_file_path, log_file_path)

    # Отмена переименования (раскомментируйте для использования)
    # undo_rename(log_file_path)
