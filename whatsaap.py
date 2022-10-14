import logging
import subprocess
import time
from pathlib import Path
from typing import Union

import qrcode as qrcode
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

logging.basicConfig(level='INFO', format='%(filename)s - %(lineno)d - %(message)s')


def auth(method_to_decorate):
    def wrapper(self, *args, **kwargs):
        self.authorisation()
        return method_to_decorate(self, *args, **kwargs)

    return wrapper


class Whatsapp:
    def __init__(self, executable_path: str = None, telegram_bot_token: str = None, telegram_admin_id: int = None,
                 wait_seconds: int = 5):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--headless')
        options.add_argument("--window-size=1080,1024")
        options.add_argument(f'--user-data-dir={Path(Path.cwd(), "User_Data")}')
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36')

        if executable_path is None:
            service = None
        else:
            service = Service(executable_path=executable_path)

        self.driver = webdriver.Chrome(
            service=service,
            options=options
        )
        self.telegram_bot_token = telegram_bot_token
        self.telegram_admin_id = telegram_admin_id
        self.wait = WebDriverWait(self.driver, wait_seconds)

    def authorisation(self):
        last_qr_code_data = ''
        while True:
            if self.auth_status():
                break
            else:
                qr_code_data = self.get_qr_code_data()
                if last_qr_code_data != qr_code_data and qr_code_data:
                    last_qr_code_data = qr_code_data
                    self.send_qr_code_to_telegram(qr_code_data)
                time.sleep(3)

    def auth_status(self) -> bool:
        while True:
            # Проверка на состояние прогрузки страницы
            try:
                self.driver.find_element(By.XPATH, '//div[@class="QgIWN"]')
                logging.info('Страница прогрузки')
                time.sleep(3)
                continue
            except NoSuchElementException:
                logging.info('Страница прогрузки не найдена')
            except Exception as err:
                logging.info(f"Неизвестная ошибка: \n {err}")

            try:
                self.driver.find_element(By.XPATH, '//header[@data-testid="chatlist-header"]')
                logging.info('Страница пользователя')
                return True
            except NoSuchElementException:
                logging.info('Страница пользователя не найдена')
            except Exception as err:
                logging.info(f"Неизвестная ошибка: \n {err}")

            try:
                self.driver.find_element(By.XPATH, '//div[@class="landing-header"]')
                logging.info('Страница авторизации')
                return False
            except NoSuchElementException:
                logging.info('Страница авторизации не найдена')
            except Exception as err:
                logging.info(f"Неизвестная ошибка: \n {err}")

            try:
                cansel_button = self.driver.find_element(By.XPATH, '//div[@data-testid="popup-controls-cancel"]')
                logging.info('Страница ошибки загрузки')
                cansel_button.click()
                logging.info('Кнопка Log Out нажата')
                continue
            except NoSuchElementException:
                logging.info('Страница ошибки загрузки не найдена')
            except Exception as err:
                logging.info(f"Неизвестная ошибка: \n {err}")

            logging.info('Ни одно из состояний не найдено')
            return False

    def get_qr_code_data(self) -> Union[str, None]:
        try:
            refresh_qr_code_button = self.driver.find_element(By.XPATH, '//button[@class="_2znac"]')
            logging.info('Кнопка перезагрузки устаревшего qr code')
            refresh_qr_code_button.click()
            logging.info('Кнопка перезагрузки устаревшего qr code нажата')
        except NoSuchElementException:
            logging.info('Кнопка перезагрузки устаревшего qr code не найдена')
        except Exception as err:
            logging.info(f"Неизвестная ошибка: \n {err}")

        try:
            qr_code_data = self.driver.find_element(By.XPATH, '//div[@data-testid="qrcode"]').get_attribute(
                "data-ref")
            logging.info(f'qr_code_data: {qr_code_data}')
            return qr_code_data
        except NoSuchElementException:
            logging.info('qr_code_data не найден')
            return None
        except Exception as err:
            logging.info(f"Неизвестная ошибка: \n {err}")
            return None

    def send_qr_code_to_telegram(self, qr_code_data: str) -> bool:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(Path(Path.cwd(), '../qrcode.png'))

        qrcode_file = Path(Path.cwd(), '../qrcode.png')
        if self.telegram_admin_id and self.telegram_bot_token:
            command = 'curl -s -X POST https://api.telegram.org/bot' \
                      + self.telegram_bot_token + '/sendPhoto -F chat_id=' + str(self.telegram_admin_id) \
                      + " -F photo=@" + str(qrcode_file)

            subprocess.call(command.split(' '),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT)
            logging.info('Попытка отправить qr code выполнена')
            return True
        else:
            logging.info(
                'Невозможно отправить QR-code для авторизации: telegram_admin_id или telegram_bot_token отсутсвуют')
            return False

    def run(self):
        url = "https://web.whatsapp.com/"
        self.driver.get(url)
        self.authorisation()

    def finish(self):
        self.driver.close()

    def go_to_user_chat(self, user_name: str) -> bool:
        if self.select_user_chat(user_name):
            return True
        else:
            return self.select_new_user_chat(user_name)

    def clear_search_input(self, search_form_user_chat: WebElement) -> bool:
        search_form_user_chat.clear()

        try:
            clear_button = self.wait.until(ec.element_to_be_clickable((By.XPATH, f'//span[@data-testid="x-alt"]')))
            logging.info(f'Кнопка очистки формы поиска чата присутствует')
            clear_button.click()
            logging.info(f'Кнопка очистки формы поиска чата нажата')
            return True
        except TimeoutException:
            logging.info(f'Кнопка очистки формы поиска чата не найдена или не кликабелена')
        except Exception as err:
            logging.info(f'Неизвестная ошибка: \n {err}')

        return False

    def select_user_chat(self, user_name: str, search_form_user_chat: WebElement = None) -> bool:
        try:
            user_chat = self.wait.until(ec.element_to_be_clickable((By.XPATH, f'//span[@title="{user_name}"]')))
            logging.info(f'Чат с пользователем {user_name} присутствует')
            user_chat.click()
            logging.info(f'Чат с пользователем {user_name} выбран')
            return True
        except TimeoutException:
            logging.info(f'Чат с пользователем {user_name} не найден или не кликабелен')
        except Exception as err:
            logging.info(f'Неизвестная ошибка: \n {err}')
        finally:
            if search_form_user_chat:
                self.clear_search_input(search_form_user_chat)
                logging.info(f'search_form_user_chat очищен после поиска')

        return False

    def select_new_user_chat(self, user_name: str):
        try:
            search_form_user_chat = self.driver.find_element(By.XPATH, '//div[@data-testid="chat-list-search"]')
            logging.info(f'Форма поиска чата найдена')
            self.clear_search_input(search_form_user_chat)
            logging.info(f'search_form_user_chat очищен до поиска')
            search_form_user_chat.send_keys(user_name)
            logging.info(f'user_name добавлен в форму поиска чата')
            return self.select_user_chat(user_name, search_form_user_chat)
        except NoSuchElementException:
            logging.info(f'Форма поиска чата не найдена')
        except Exception as err:
            logging.info(f'Неизвестная ошибка: \n {err}')
        return False

    def get_input_form_chat(self, user_name: str) -> Union[WebElement, None]:
        try:
            input_form = self.wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH, '//div[@data-testid="compose-box"]//div[@contenteditable="true"]'))
            )
            logging.info(f'Форма отправки сообщений пользователю {user_name} присутствует')
            input_form.click()
            logging.info(f'Форма отправки сообщений пользователю {user_name} выбрана')
            return input_form
        except TimeoutException:
            logging.info(f'Форма отправки сообщений пользователю {user_name} не найдена или не кликабельна')
        except Exception as err:
            logging.info(f'Неизвестная ошибка: \n {err}')
        return None

    @staticmethod
    def input_in_form_chat(input_form_chat: WebElement, text: str):
        try:
            input_form_chat.clear()
            logging.info(f'input_form_chat очищен')
            input_form_chat.send_keys(text)
            logging.info(f'В input_form_chat текст вставлен')
        except Exception as err:
            logging.info(f'Неизвестная ошибка: \n {err}')
            return

    def click_send_button(self):
        try:
            send_button = self.wait.until(
                ec.element_to_be_clickable((By.XPATH,
                                            '//div[@data-testid="compose-box"]'
                                            '//button[@data-testid="compose-btn-send"]'))
            )
            logging.info(f'Кнопка отправки сообщения найдена')
            send_button.click()
            logging.info(f'Кнопка отправки сообщения нажата')
        except NoSuchElementException:
            logging.info(f'Кнопка отправки сообщения не найдена')
        except Exception as err:
            logging.info(f'Неизвестная ошибка: \n {err}')

    @auth
    def send_message(self, user_name: str, text: str) -> bool:
        if user_name and text:
            if self.go_to_user_chat(user_name):
                input_form_chat = self.get_input_form_chat(user_name)
                if input_form_chat:
                    self.input_in_form_chat(input_form_chat, text)
                    self.click_send_button()
                    return True
                else:
                    return False

            else:
                logging.info(f'"{user_name}" not in Phone Book')
                return False
        else:
            logging.info('"user_name" and "text" not be empty')
            return False
