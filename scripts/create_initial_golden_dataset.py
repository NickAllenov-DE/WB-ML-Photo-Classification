# Импорт библиотек
import os
import pandas as pd

def create_initial_golden_dataset(feedback_csv_path, photo_dir_path, output_csv_path):
    """Создает начальный золотой датасет, сохраняя строки, 
    где путь к фото совпадает с файлами в указанной директории.
    """
    
    # Чтение CSV файла с отзывами
    feedback_df = pd.read_csv(feedback_csv_path)
    
    # Проверка наличия необходимых колонок
    required_columns = {'local_path', 'product_url'}
    if not required_columns.issubset(feedback_df.columns):
        print(f"Ошибка: Ожидаемые колонки {required_columns} отсутствуют в CSV-файле.")
        return

    # Получение списка имен файлов в директории golden_dataset_photos
    golden_filenames = set(os.listdir(photo_dir_path))

    # Фильтрация строк, где filename из CSV совпадает с файлами в golden_dataset_photos
    feedback_df['filename'] = feedback_df['local_path'].apply(lambda x: os.path.basename(x))
    filtered_df = feedback_df[feedback_df['filename'].isin(golden_filenames)]

    # Найти отсутствующие файлы
    filtered_filenames = set(filtered_df['filename'])
    missing_files = golden_filenames - filtered_filenames

    if missing_files:
        print("Отсутствующие файлы в итоговом датасете:")
        for file in missing_files:
            print(file)
    else:
        print("Все файлы из golden_dataset_photos найдены в итоговом датасете.")

    # Удаление ненужных колонок
    golden_df = filtered_df.drop(columns=['product_url', 'local_path'])

    # Сохранение отфильтрованного DataFrame в новый CSV файл
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    golden_df.to_csv(output_csv_path, index=False)
    
    print(f"Создание начального датасета завершено. Файл сохранен как '{output_csv_path}'.")



# Путь к файлам
feedback_csv_path = r'd:\Projects\CurrentProjects\WB-ML-Photo-Classification\feedback_images.csv'
photo_dir_path = r'd:\Projects\CurrentProjects\WB-ML-Photo-Classification\golden_dataset_photos'
output_csv_path = r'd:\projects\currentprojects\wb-ml-photo-classification\golden_dataset_initial.csv'

if __name__ == '__main__':
    create_initial_golden_dataset(feedback_csv_path, photo_dir_path, output_csv_path)
