# Импорт библиотек и модулей
import requests
import os
import sys
import codecs
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import csv

# Обработка кодировки
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
start_page_url = "https://www.wildberries.ru/catalog/detyam/tovary-dlya-malysha/podguzniki/podguzniki-detskie"


# Настройка Selenium WebDriver
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")                               # Открыть браузер в полном окне
    options.add_argument("--disable-blink-features=AutomationControlled")   # Меньше детектирования Selenium
    options.add_argument(f"user-agent={USER_AGENT}")                        # Добавляем кастомный User-Agent
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


# Прокрутка страницы для загрузки всех элементов
def scroll_page_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")    # Прокрутка страницы вниз
        time.sleep(random.uniform(1.5, 3.5))  # Ожидание загрузки новой части страницы
        new_height = driver.execute_script("return document.body.scrollHeight")  # Проверка, достигнута ли нижняя часть страницы
        if new_height == last_height:
            break
        last_height = new_height


def scroll_popup_to_bottom(driver, popup_element, scroll_pause_time=1):
    """ Функция для прокрутки всплывающего окна с фотографиями """
    last_height = driver.execute_script("return arguments[0].scrollHeight", popup_element)
    
    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", popup_element)
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return arguments[0].scrollHeight", popup_element)
        if new_height == last_height:
            break
        last_height = new_height


# Функция для прокрутки страницы на "increment" высоты
def scroll_page_incrementally(driver, increment: float):
    start_height = driver.execute_script("return document.body.scrollHeight")   # Сохраняем начальную высоту страницы

    scroll_increment = int(start_height * increment)
    new_scroll_position = 0
    while new_scroll_position < scroll_increment:
        driver.execute_script(f"window.scrollTo(0, {new_scroll_position});")
        new_scroll_position += 2  # Увеличиваем позицию прокрутки на 2 пикселей (можно настроить)


# Функция для проверки наличия кнопки "Следующая страница" и возврата её, если найдена
def get_next_page_button(driver):
    try:
        next_button = driver.find_element(By.XPATH, '//*[@class="pagination-next pagination__next j-next-page"]')
        return next_button
    except Exception as e:
        print("Кнопка следующей страницы не найдена:", e)
        return None


# Функция для сбора ссылок на карточки товаров
def get_product_links(driver, start_page):
    product_links = []
    page_number = 1

    while True:
        print(f"Собираем ссылки со страницы {page_number}")
        driver.get(f"{start_page}?page={page_number}")
        time.sleep(random.uniform(1.5, 3.5))  
        
        scroll_page_to_bottom(driver)
        
        # Находим все ссылки на карточки товаров
        products = driver.find_elements(By.XPATH, '//article/div/a')
        for product in products:
            product_links.append(product.get_attribute("href"))

        # Проверяем наличие кнопки "Следующая страница"
        next_button = get_next_page_button(driver)
        if next_button:
            next_button.click()     # Если кнопка найдена, кликаем по ней
            time.sleep(random.uniform(1.5, 3.5))  
            page_number += 1
        else:
            break

    return product_links


# Функция для загрузки изображения по URL
def download_image(img_url, save_directory, img_name):
    try:
        img_data = requests.get(img_url).content
        img_path = os.path.join(save_directory, img_name)
        with open(img_path, 'wb') as img_file:
            img_file.write(img_data)
        return img_path
    except Exception as e:
        print(f"Ошибка при сохранении изображения: {e}")
        return None


def get_feedback_images(driver, product_card_url, save_directory, csv_writer, index, existing_images):
    driver.get(product_card_url)  # Заходим на страницу товара
    time.sleep(random.uniform(1.5, 3.5))  # Ожидаем загрузку страницы

    # Прокрутка страницы для загрузки контента
    scroll_page_incrementally(driver, 0.1)
    time.sleep(1)

    # Попытка найти и нажать на кнопку "Смотреть все фото и видео"
    try:
        show_all_photos_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@class="comments__user-opinion-right hide-mobile"]/button'))
        )
        show_all_photos_button.click()  # Пытаемся нажать на кнопку
        time.sleep(random.uniform(1.5, 3.5))  # Ждем, пока откроется окно с фотографиями
    except Exception as e:
        print(f"Кнопка 'Смотреть все фото и видео' не найдена для товара: {product_card_url}, ошибка: {e}")
        return

    # Прокрутка всплывающего окна с фотографиями
    try:
        popup_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div'))
        )
        
        # ВНИМАНИЕ!!! ОСТОРОЖНО!!!
        # Эта функция для прокрутки всплывающего окна с фото, если нужны все 3 МИЛЛИОНА фото
        # scroll_popup_to_bottom(driver, popup_element)

        # Сбор всех ссылок на фотографии из отзывов
        images = popup_element.find_elements(By.XPATH, './/li/img')
        print(f"Найдено {len(images)} фото для товара: {product_card_url}")

        # Создание директории для сохранения изображений, если её ещё нет
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        # Сохранение фотографий и запись данных в CSV
        for img_index, img in enumerate(images):
            img_url = img.get_attribute('src')

            # Проверка на дубликаты
            if img_url not in existing_images:
                existing_images.add(img_url)  # Добавляем URL в множество
                img_name = f"product_{index + 1}_{img_index + 1}.jpg"
                img_path = download_image(img_url, save_directory, img_name)

                if img_path:
                    csv_writer.writerow([f"{index + 1}_{img_index + 1}", product_card_url, img_url, img_path])
            else:
                print(f"Дубликат изображения пропущен: {img_url}")

    except Exception as e:
        print(f"Ошибка при загрузке фотографий для товара {product_card_url}: {e}")



# Основная функция
def main():
    driver = setup_driver()  # Запуск браузера
    csv_file = "feedback_images.csv"  # Название CSV-файла
    dir_to_save = os.path.join(os.getcwd(), "wb-diapers-photos")

    # Открытие CSV-файла в режиме записи
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file, delimiter=';')
        csv_writer.writerow(['Индекс', 'URL карточки товара', 'URL фотографии', 'Путь к фото на компьютере'])  # Заголовки

        existing_images = set()  # Множество для хранения уникальных URL изображений

        try:
            product_cards_list = get_product_links(driver, start_page_url)
            for index, product_card in enumerate(product_cards_list):
                get_feedback_images(driver, product_card, dir_to_save, csv_writer, index, existing_images)
        finally:
            driver.quit()  # Закрытие браузера



if __name__ == "__main__":
    main()
