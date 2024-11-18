# Импорт библиотек
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
import os
import csv

# Параметры
data_dir = 'data'
num_epochs = 10
batch_size = 32
learning_rate = 0.001

# Загрузка и предобработка данных
train_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

val_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

train_data = datasets.ImageFolder(os.path.join(data_dir, 'train'), transform=train_transforms)
val_data = datasets.ImageFolder(os.path.join(data_dir, 'val'), transform=val_transforms)

train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_data, batch_size=batch_size, shuffle=False)

# Загрузка модели ResNet-34
model = models.resnet34(pretrained=True)
num_features = model.fc.in_features
model.fc = nn.Linear(num_features, len(train_data.classes))  # Соответствие числу категорий
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# Загрузка весов существующей модели, если файл существует
if os.path.exists('models/resnet34_baseline.pth'):
    model.load_state_dict(torch.load('models/resnet34_baseline.pth'))
    print("Модель загружена из 'resnet34_baseline.pth'")
else:
    print("Файл модели не найден, начинаем обучение с нуля.")

# Функция потерь и оптимизатор
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

# Создание объекта SummaryWriter для TensorBoard
writer = SummaryWriter('runs/resnet34_baseline_experiment')

# Создание файла для записи результатов в текстовом формате и CSV
results_file_txt = 'training_results.txt'
results_file_csv = 'training_results.csv'

# Запись заголовка в CSV-файл
with open(results_file_csv, 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["Epoch", "Loss", "Validation Loss", "Accuracy"])  # Заголовок

# Запись заголовка в текстовый файл
with open(results_file_txt, 'w') as f:
    f.write("Epoch, Loss, Validation Loss, Accuracy\n")  # Заголовок

# Тренировка модели
for epoch in range(num_epochs):
    model.train()
    running_loss = 0.0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()

    epoch_loss = running_loss / len(train_loader)

    # Оценка на валидационном наборе
    model.eval()
    val_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = 100 * correct / total

    # Запись результатов в текстовый файл
    with open(results_file_txt, 'a') as f:
        f.write(f"{epoch+1}, {epoch_loss:.4f}, {val_loss/len(val_loader):.4f}, {accuracy:.2f}%\n")
    
    # Запись результатов в CSV-файл
    with open(results_file_csv, 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([epoch+1, epoch_loss, val_loss/len(val_loader), accuracy])  # Данные

    # Запись в TensorBoard
    writer.add_scalar('Loss/train', epoch_loss, epoch)
    writer.add_scalar('Loss/val', val_loss/len(val_loader), epoch)
    writer.add_scalar('Accuracy/val', accuracy, epoch)

    print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss:.4f}, Validation Loss: {val_loss/len(val_loader):.4f}, Accuracy: {accuracy:.2f}%')

# Сохранение модели
torch.save(model.state_dict(), 'models/resnet34_baseline.pth')
print("Модель сохранена как 'resnet34_baseline.pth'")

# Закрытие writer для TensorBoard
writer.close()
