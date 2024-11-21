# Импорт библиотек и модулей

import requests  # Для выполнения HTTP-запросов
import os  # Для работы с операционной системой
import sys  # Для доступа к параметрам и функциям интерпретатора Python
import codecs  # Для работы с кодировками
from urllib.parse import urljoin  # Для объединения URL
from selenium import webdriver  # Для работы с браузером через Selenium
from selenium.webdriver.common.by import By  # Для поиска элементов на странице
from selenium.webdriver.chrome.service import Service  # Для управления службой ChromeDriver
from webdriver_manager.chrome import ChromeDriverManager  # Для автоматической установки ChromeDriver
from selenium.webdriver.support.ui import WebDriverWait  # Для ожидания загрузки элементов
from selenium.webdriver.support import expected_conditions as EC  # Для условий ожидания
import time  # Для работы с временем
from datetime import datetime, timedelta
import random  # Для генерации случайных чисел
import csv  # Для работы с CSV-файлами
import logging  # Для ведения логов
from tqdm import tqdm
import pandas as pd

from utils import scroll_page_to_bottom, scroll_page_incrementally, scroll_popup_to_bottom,\
    get_next_page_button
from products import get_product_links, get_price, get_full_description_button,\
    get_description_data, get_product_data, save_product_data_to_parquet
from reviews import extract_date_time, get_author_name, get_review_date_and_rating,\
    get_review_text, get_reviews_with_photos, save_review_data_to_parquet, download_images_from_reviews

TIMEOUT = (0.5, 2.0)

# Обработка кодировки для вывода в консоль
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Пользовательский агент для имитации браузера
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
# URL начальной страницы для парсинга
start_page_url = "https://www.wildberries.ru/catalog/detyam/tovary-dlya-malysha/podguzniki/podguzniki-detskie"


def setup_logging(log_file: str = "wb_parser.log") -> None:
    """Настраивает логирование."""
    logging.basicConfig(
        level=logging.INFO,     # Уровень логирования
        format="%(asctime)s - %(levelname)s - %(message)s", # Формат сообщений
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),  # Логирование в файл
        logging.StreamHandler()  # Логирование в консоль
        ]
    )
    logging.info("Логирование настроено.")


def setup_driver():
    """Настраивает и возвращает экземпляр Selenium WebDriver с заданными параметрами."""
    logging.info("Настройка веб-драйвера.")
    options = webdriver.ChromeOptions()  # Создание объекта с опциями для Chrome
    options.add_argument("--start-maximized")  # Запуск браузера в максимизированном режиме
    options.add_argument("--disable-blink-features=AutomationControlled")  # Отключение автоматического управления
    options.add_argument(f"user-agent={USER_AGENT}")  # Установка пользовательского агента
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)  # Инициализация драйвера
    return driver  # Возврат настроенного драйвера


def main():
    """Основная функция для запуска процесса парсинга и сохранения данных."""
    setup_logging()
    logging.info("Запуск основного процесса.")
    driver = setup_driver()  # Настройка веб-драйвера
    product_parquet_file = r"d:\Projects\CurrentProjects\WB-ML-Photo-Classification\products_data.parquet"  # Путь для сохранения данных о товарах
    review_parquet_file = r"d:\Projects\CurrentProjects\WB-ML-Photo-Classification\reviews_data.parquet"  # Путь для сохранения данных о отзывах
    dir_to_save = r"d:\Projects\CurrentProjects\WB-ML-Photo-Classification\wb-diapers-photos"  # Директория для сохранения изображений

    try:
        # Получение ссылок на карточки товаров
        logging.info("Начало сбора ссылок на карточки товаров.")
        product_cards_list = get_product_links(driver, start_page_url)
        logging.info(f"Собрано {len(product_cards_list)} ссылок на карточки товаров.")
        
        # Проход по каждой карточке товара
        for product_card in product_cards_list:
            try:
                # Сбор данных о товаре
                product_data = get_product_data(driver, product_card)
                save_product_data_to_parquet(product_data, product_parquet_file)
                logging.info(f"Данные о товаре сохранены: {product_data['name']}")
                
                # Сбор данных об отзывах
                reviews_with_photos = get_reviews_with_photos(driver)
                save_review_data_to_parquet(reviews_with_photos, review_parquet_file)
                logging.info(f"Данные о {len(reviews_with_photos)} отзывах сохранены.")
            except Exception as e:
                logging.error(f"Ошибка обработки карточки товара {product_card}: {e}")
        
        # Скачивание изображений из сохраненного файла отзывов
        logging.info("Начало скачивания изображений из отзывов.")
        if os.path.exists(review_parquet_file):
            download_images_from_reviews(review_parquet_file, dir_to_save)
            logging.info(f"Изображения успешно скачаны в директорию: {dir_to_save}")
        else:
            logging.warning(f"Файл отзывов {review_parquet_file} не найден. Пропуск скачивания изображений.")
    
    except Exception as e:
        logging.error(f"Ошибка в основном процессе: {e}")
    finally:
        # Закрытие драйвера
        driver.quit()
        logging.info("Процесс завершен.")



if __name__ == "__main__":
    main()
