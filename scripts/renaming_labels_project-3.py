import pandas as pd

# Загрузите CSV-файл
csv_path = r"D:\Projects\CurrentProjects\WB-ML-Photo-Classification\data\annotations\label_studio\project-3-at-2024-10-29-22-16-904fedbe.csv"
df = pd.read_csv(csv_path)

# Словарь с новыми названиями меток
label_mapping = {
    "Real Child": "real_child",
    "Illustration of Child": "illustrated_child",
    "No Child Present": "no_child_present",
}

# Замена старых меток на новые
df['choice'] = df['choice'].replace(label_mapping)

# Сохранение обновленного CSV
df.to_csv(csv_path, index=False)

print("Метки успешно обновлены в CSV-файле.")


# TODO: "ДОБАВИТЬ ЦИФРОВЫЕ МЕТКИ КЛАССОВ: 1, 2, 3"