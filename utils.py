
from selenium.webdriver.common.by import By  # Для поиска элементов на странице
import logging  # Для ведения логов
import time  # Для работы с временем
import random  # Для генерации случайных чисел
TIMEOUT = (0.5, 2.0)


def scroll_page_to_bottom(driver, scroll_percentage=0.2):
    """Прокручивает страницу на заданный процент до тех пор, пока высота страницы изменяется, затем докручивает до конца."""
    logging.info("Начинаем прокрутку страницы.")
    
    last_height = driver.execute_script("return document.body.scrollHeight")  # Получаем текущую высоту страницы
    scroll_position = 0  # Начальная позиция прокрутки
    
    while True:
        # Прокручиваем на заданный процент от текущей высоты
        driver.execute_script(f"window.scrollTo(0, {scroll_position + scroll_percentage * last_height});")
        time.sleep(random.uniform(*TIMEOUT))  # Ожидание перед следующей прокруткой

        # Получаем новую высоту страницы
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # Если высота страницы не изменилась, прокручиваем до конца
        if new_height == last_height:
            logging.info(f"Достигнут конец страницы ({scroll_percentage*100}%). Теперь прокручиваем до самого конца.")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Прокручиваем до конца
            logging.info("Достигнут конец страницы.")
            break
        
        last_height = new_height  # Обновляем высоту для следующей итерации
        scroll_position += scroll_percentage * last_height  # Обновляем позицию прокрутки


def scroll_page_incrementally(driver, increment: float):
    """Прокручивает страницу на заданное количество пикселей, основанное на проценте от высоты страницы."""
    start_height = driver.execute_script("return document.body.scrollHeight")  # Получаем начальную высоту страницы
    scroll_increment = int(start_height * increment)  # Вычисляем количество пикселей для прокрутки
    new_scroll_position = 0  # Начальная позиция прокрутки

    logging.info(f"Прокручиваем страницу на {scroll_increment} пикселей.")
    while new_scroll_position < scroll_increment:
        driver.execute_script(f"window.scrollTo(0, {new_scroll_position});")  # Прокручиваем на заданное количество пикселей
        new_scroll_position += 2  # Увеличиваем позицию прокрутки на 2 пикселя


def scroll_popup_to_bottom(driver, popup_element):
    """Прокручивает всплывающее окно до самого низа."""
    logging.info("Начинаем прокрутку всплывающего окна.")
    last_height = driver.execute_script("return arguments[0].scrollHeight", popup_element)  # Получаем высоту всплывающего окна
    
    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", popup_element)  # Прокрутка вниз
        time.sleep(random.uniform(*TIMEOUT))  # Ожидание перед следующей прокруткой
        new_height = driver.execute_script("return arguments[0].scrollHeight", popup_element)  # Получаем новую высоту
        if new_height == last_height:  # Если высота не изменилась, значит, достигли конца
            logging.info("Достигнут конец всплывающего окна.")
            break
        last_height = new_height  # Обновляем высоту для следующей итерации


def get_next_page_button(driver):
    """Возвращает кнопку 'Следующая страница', если она доступна, иначе None."""
    try:
        next_button = driver.find_element(By.XPATH, '//*[@class="pagination-next pagination__next j-next-page"]')
        logging.info("Найдена кнопка 'Следующая страница'.")
        return next_button
    except Exception as e:
        logging.warning("Кнопка 'Следующая страница' не найдена: %s", e)
        return None
