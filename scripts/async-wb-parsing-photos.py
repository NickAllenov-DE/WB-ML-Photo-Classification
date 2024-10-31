# Импорт библиотек и модулей
import requests
import os
import sys
import codecs
import logging
import aiohttp
import asyncio
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


# Настройка логирования
logging.basicConfig(filename="async-parser.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", encoding="utf-8")


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
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Прокрутка страницы вниз
        time.sleep(random.uniform(1.5, 3.5))  # Ожидание загрузки новой части страницы
        new_height = driver.execute_script("return document.body.scrollHeight")  # Проверка, достигнута ли нижняя часть страницы
        if new_height == last_height:
            break
        last_height = new_height


# Прокрутка всплывающего окна с фотографиями
def scroll_popup_to_bottom(driver, popup_element, scroll_pause_time=1):
    last_height = driver.execute_script("return arguments[0].scrollHeight", popup_element)
    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", popup_element)
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return arguments[0].scrollHeight", popup_element)
        if new_height == last_height:
            break
        last_height = new_height


# Прокрутка страницы на "increment" высоты
def scroll_page_incrementally(driver, increment: float):
    start_height = driver.execute_script("return document.body.scrollHeight")  # Сохраняем начальную высоту страницы
    scroll_increment = int(start_height * increment)
    new_scroll_position = 0
    while new_scroll_position < scroll_increment:
        driver.execute_script(f"window.scrollTo(0, {new_scroll_position});")
        new_scroll_position += 2  # Увеличиваем позицию прокрутки на 2 пикселя


# Проверка наличия кнопки следующей страницы
def get_next_page_button(driver):
    try:
        next_button = driver.find_element(By.XPATH, '//*[@class="pagination-next pagination__next j-next-page"]')
        return next_button
    except Exception as e:
        logging.error(f"Кнопка следующей страницы не найдена: {e}")
        return None


# Проверка доступности URL
def is_url_accessible(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException as e:
        logging.error(f"Ошибка доступа к URL: {url}, ошибка: {e}")
        return False


# Асинхронная загрузка изображения
async def async_download_image(session, img_url, save_directory, img_name):
    try:
        async with session.get(img_url) as response:
            if response.status == 200:
                img_data = await response.read()
                img_path = os.path.join(save_directory, img_name)
                with open(img_path, 'wb') as img_file:
                    img_file.write(img_data)
                logging.info(f"Изображение успешно сохранено: {img_path}")
                return img_path
            else:
                logging.error(f"Не удалось загрузить изображение. Статус: {response.status}")
                return None
    except Exception as e:
        logging.error(f"Ошибка при сохранении изображения: {e}")
        return None


# Получение ссылок на карточки товаров
def get_product_links(driver, start_page):
    product_links = []
    page_number = 1

    while True:  # Можно заменить "True" на "page_number < 2" и "< 2" на нужное количество страниц
        logging.info(f"Собираем ссылки со страницы {page_number}")
        driver.get(f"{start_page}?page={page_number}")
        time.sleep(random.uniform(1.5, 3.5))  # Увеличьте время ожидания
        scroll_page_to_bottom(driver)
        
        products = driver.find_elements(By.XPATH, '//article/div/a')
        for product in products:
            link = product.get_attribute("href")
            if link not in product_links:
                product_links.append(link)

        next_button = get_next_page_button(driver)
        if next_button:
            next_button.click()  # Переходим на следующую страницу
            time.sleep(random.uniform(1.5, 3.5))  # Увеличьте время ожидания
            page_number += 1
        else:
            break
    return product_links



def scroll_into_view(driver, element):
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    time.sleep(1)  # Добавляем небольшую задержку, чтобы страница стабилизировалась



def wait_for_element_to_be_clickable(driver, xpath, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        return element
    except Exception as e:
        logging.error(f"Элемент не кликабелен: {xpath}, ошибка: {e}")
        return None


def click_element_js(driver, element):
    driver.execute_script("arguments[0].click();", element)


async def async_get_feedback_images(driver, product_card_url, save_directory, csv_writer, index, existing_images):
    if is_url_accessible(product_card_url):
        driver.get(product_card_url)
        await asyncio.sleep(random.uniform(1.5, 3.5))

        scroll_page_incrementally(driver, 0.1)
        await asyncio.sleep(1.5)

        try:
            # Ожидание и прокрутка до кнопки
            show_all_photos_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@class="comments__user-opinion-right hide-mobile"]/button'))
            )
            
            # show_all_photos_button = wait_for_element_to_be_clickable(driver, '//*[@class="comments__user-opinion-right hide-mobile"]/button')
            
            if show_all_photos_button:
                show_all_photos_button.click()  # Пытаемся нажать на кнопку

                # scroll_into_view(driver, show_all_photos_button)  # Прокрутить поле видимости дна кнопку
                click_element_js(driver, show_all_photos_button)  # Принудительное нажатие кнопки через скрипт js

                await asyncio.sleep(random.uniform(2, 3.5))
            else:
                logging.error(f"Кнопка 'Смотреть все фото и видео' не найдена для товара: {product_card_url}")
                return
        except Exception as e:
            logging.error(f"Ошибка при клике по кнопке для товара: {product_card_url}, ошибка: {e}")
            return

        # Далее код для обработки всплывающего окна с фото
        popup_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div'))
        )

        # ВНИМАНИЕ!!! ОСТОРОЖНО!!!
        # Эта функция для прокрутки всплывающего окна с фото, если нужны все 3 МИЛЛИОНА фото
        # scroll_popup_to_bottom(driver, popup_element)

        images = popup_element.find_elements(By.XPATH, './/li/img')
        logging.info(f"Найдено {len(images)} фото для товара: {product_card_url}")

        # Создание директории для сохранения изображений, если её ещё нет
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        async with aiohttp.ClientSession() as session:
            tasks = []
            for img_index, img in enumerate(images):
                img_url = img.get_attribute('src')

                if img_url not in existing_images:
                    existing_images.add(img_url)
                    img_name = f"product_{index + 1}_{img_index + 1}.jpg"
                    tasks.append(async_download_image(session, img_url, save_directory, img_name))

            results = await asyncio.gather(*tasks)

            for img_path in results:
                if img_path:
                    csv_writer.writerow([f"{index + 1}", product_card_url, img_url, img_path])
    else:
        logging.error(f"URL недоступен: {product_card_url}")


# Основная асинхронная функция
async def main():
    driver = setup_driver()
    csv_file = "feedback_images_async.csv"
    dir_to_save = os.path.join(os.getcwd(), "wb-diapers-photos-async")

    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file, delimiter=';')
        csv_writer.writerow(['Индекс', 'URL карточки товара', 'URL фотографии', 'Локальный путь к фото'])

        existing_images = set()

        try:
            product_cards_list = get_product_links(driver, start_page_url)
            tasks = []
            for index, product_card in enumerate(product_cards_list):
                tasks.append(async_get_feedback_images(driver, product_card, dir_to_save, csv_writer, index, existing_images))

            await asyncio.gather(*tasks)
        finally:
            driver.quit()



if __name__ == "__main__":
    asyncio.run(main())
