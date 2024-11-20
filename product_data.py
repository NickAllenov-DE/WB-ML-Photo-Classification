
import os  # Для работы с операционной системой
from urllib.parse import urljoin  # Для объединения URL
from selenium.webdriver.common.by import By  # Для поиска элементов на странице
from selenium.webdriver.support.ui import WebDriverWait  # Для ожидания загрузки элементов
from selenium.webdriver.support import expected_conditions as EC  # Для условий ожидания
import time  # Для работы с временем
import random  # Для генерации случайных чисел
import logging  # Для ведения логов
import pandas as pd

from utils import scroll_page_to_bottom, get_next_page_button
from product_data import get_price, get_full_description_button, get_description_data
TIMEOUT = (0.5, 2.0)

def get_product_links(driver, start_page):
    """Собирает ссылки на карточки товаров со страниц, начиная с заданного URL."""
    product_links = []  # Список для хранения ссылок на товары
    page_number = 1  # Номер текущей страницы

    while True:
        current_page_url = f"{start_page}?page={page_number}"
        
        logging.info(f"Собираем ссылки со страницы {page_number} ({current_page_url}).")
        driver.get(current_page_url)  # Переход на страницу
        time.sleep(random.uniform(*TIMEOUT))  # Ожидание загрузки страницы
        scroll_page_to_bottom(driver)  # Прокрутка страницы до конца

        # Поиск элементов с товарами
        products = driver.find_elements(By.XPATH, '//article/div/a')
        if not products:
            logging.warning(f"На странице {page_number} не найдено товаров. Прерывание.")
            break

        # Получение ссылок
        page_links = [product.get_attribute("href") for product in products if product.get_attribute("href")]
        logging.info(f"На странице {page_number} найдено {len(page_links)} ссылок.")

        product_links.extend(page_links)  # Добавление ссылок в общий список

        # Проверяем наличие кнопки "Следующая страница"
        next_button = get_next_page_button(driver)
        if next_button:
            logging.info("Переход на следующую страницу.")
            next_button.click()  # Переход на следующую страницу
            time.sleep(random.uniform(*TIMEOUT))  # Ожидание загрузки следующей страницы
            page_number += 1  # Увеличение номера страницы
        else:
            logging.info("Последняя страница достигнута. Завершаем сбор ссылок.")
            break

    logging.info(f"Сбор завершён. Всего собрано {len(product_links)} ссылок.")
    return product_links  # Возврат списка ссылок на товары


def get_price(driver):
    """Извлекает и форматирует цену товара."""
    try:
        price_element = driver.find_element(By.XPATH, '//*[@class="product-page__price-block product-page__price-block--common hide-mobile"]/div/div/div/div/p/span/ins')
        price_text = price_element.text  # Например, "1 234 ₽"
        price = int(price_text.replace("\u00A0", "").replace("₽", "").strip())  # Убираем пробелы и знак рубля
        return price
    except Exception as e:
        logging.error(f"Не удалось извлечь цену: {e}")
        return None


def get_full_description_button(driver):
    """Нажимает на кнопку 'Все характеристики и описание', чтобы открыть всплывающее окно с полными характеристиками."""
    try:
        button = driver.find_element(By.XPATH, '//button[contains(text(), "Все характеристики и описание")]')
        button.click()
        logging.info("Кнопка 'Все характеристики и описание' найдена и нажата.")
        time.sleep(random.uniform(*TIMEOUT))  # Ожидание открытия всплывающего окна
    except Exception as e:
        logging.error(f"Не удалось найти или нажать кнопку 'Все характеристики и описание': {e}")


def get_description_data(driver):
    """Извлекает данные из всплывающего окна после его открытия."""
    try:
        # Подождем загрузку окна
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div')))
        
        # Находим каждый элемент внутри окна по его XPATH и извлекаем данные
        color = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[1]/tbody/tr/td/span').text
        product_type = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[3]/tbody/tr[1]/td/span').text
        number_units = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[2]/tbody/tr/td/span').text
        weight_category = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[3]/tbody/tr[2]/td/span').text
        producing_country = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[3]/tbody/tr[4]/td/span').text

        # Извлечение размеров упаковки
        length = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[4]/tbody/tr[1]/td/span').text.strip().replace(' см', '')
        height = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[4]/tbody/tr[2]/td/span').text.strip().replace(' см', '')
        width = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[4]/tbody/tr[3]/td/span').text.strip().replace(' см', '')
        
        # Форматируем габариты
        overall_size = f"{width}x{height}x{length}"

        description = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/section/p').text

        popup_data = {
            "color": color,
            "diapers_type": product_type,
            "number_of_units": number_units,
            "weight_category": weight_category,
            "producing_country": producing_country,
            "overall_size": overall_size,
            "description": description
        }
        return popup_data
    except Exception as e:
        logging.error(f"Ошибка при извлечении данных из всплывающего окна: {e}")
        return None


def get_product_data(driver, product_url):
    """Извлекает всю информацию о товаре, включая данные из всплывающего окна."""
    driver.get(product_url)
    time.sleep(random.uniform(*TIMEOUT))
    
    # Основные данные на странице товара
    product_id = driver.find_element(By.XPATH, '//*[@id="productNmId"]').text
    brand = driver.find_element(By.XPATH, '//*[@class="product-page__header"]/a').text
    name = driver.find_element(By.XPATH, '//*[@class="product-page__header"]/h1').text
    price = get_price(driver)  # Используем отдельную функцию для цены

    # Открываем всплывающее окно и извлекаем данные
    get_full_description_button(driver)
    popup_data = get_description_data(driver)
    
    # Объединяем данные
    product_data = {
        "product_article": product_id,
        "brand": brand,
        "name": name,
        "price": price
    }
    
    # Если данные из всплывающего окна успешно получены, добавляем их к product_data
    if popup_data:
        product_data.update(popup_data)
    
    return product_data


def save_product_data_to_parquet(product_data, parquet_file):
    """Сохраняет данные о товаре в файл products.parquet."""
    try:
        # Создаем DataFrame для добавления данных о товаре
        df_product = pd.DataFrame([product_data])
        
        # Если файл существует, то добавляем новые данные, иначе создаем новый
        if os.path.exists(parquet_file):
            df_product.to_parquet(parquet_file, append=True, index=False)
        else:
            df_product.to_parquet(parquet_file, index=False)
        
        logging.info(f"Данные о товаре сохранены в {parquet_file}.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных о товаре: {e}")
