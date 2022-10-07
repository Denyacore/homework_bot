import os
import sys
import requests
import time
import logging
import exceptions
import json

from http import HTTPStatus
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler


import telegram

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(funcName)s - [%(levelname)s] - %(message)s'
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler = RotatingFileHandler('main.log',
                              maxBytes=50000000,
                              backupCount=5,
                              encoding='UTF-8'
                              )
logger.addHandler(handler)


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат,
    определяемый переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра: 
    экземпляр класса Bot
    и строку с текстом сообщения."""

    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Отправлено сообщение с текстом: {message}')
    except telegram.error.TelegramError:
        logger.error(f'Сообщение не отправлено')
        raise telegram.error.TelegramError(f'Сообщение не отправлено')


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра функция получает временную метку.
    В случае успешного запроса должна вернуть ответ API,
    преобразовав его из формата JSON к типам данных Python.
    """
    logging.info(f'Отпрравляем запрос к API и получаем ответ')
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        logger.info(f'Отправлен запрос к API'
                    f'\nКод ответа {response.status_code}')
        if response.status_code != HTTPStatus.OK:
            print('Что то с api')
            logger.error(f'Что то с API')
            raise response.raise_for_status()
    except requests.exceptions.RequestException as error:
        message = f'Эндпойнт недоступен: {error}'
        logger.error(message)
        raise requests.exceptions.RequestException(message)
    except json.decoder.JSONDecodeError as error:
        raise Exception((f'Ответ {response.text} получен не в виде JSON: '
                         f'{error}'))
    answer_api = response.json()
    answer_api_succsess = f'Получен ответ API с типом данных {type(answer_api)}'
    logger.info(answer_api_succsess)
    print(answer_api_succsess)
    return answer_api


def check_response(answer_api):
    """Проверяет ответ API на корректность. 
    В качестве параметра функция получает ответ API, приведенный к типам данных Python.
    Если ответ API соответствует ожиданиям, 
    то функция должна вернуть список домашних работ (он может быть и пустым),
    доступный в ответе API по ключу 'homeworks'.
    """
    logging.info(f'Проверяем корректность ответа API')
    if isinstance(answer_api, dict):
        try:
            homework_list = (answer_api['homeworks'])
            logger.info(f'Получен список домашек типа {type(homework_list)}')
            # print (f'Получен список домашек с нужным типом {type(homework_list)} ')
        except KeyError as error:
            logger.error(f'В ответе не обнаружен ключ {error}')
            raise exceptions.KeyNotFound(f'В ответе не обнаружен ключ {error}')
        if homework_list == []:
            print(f'Список домашек пуст')
            raise TypeError(f'Список домашек для доработки пуст')
        homework = homework_list[0]
        logger.info(f'Получена домашка для доработки типа {type(homework)}')
        return homework
    else:
        print(f'Ответ API не содержит словарь')
        raise TypeError(f'Ответ API не содержит словарь')


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка домашних работ.
    В случае успеха, функция возвращает подготовленную для отправки в Telegram строку,
    содержащую один из вердиктов словаря HOMEWORK_STATUSES.
    """
    logging.info(f'Извлекаем статус и имя домашки')
    if 'homework_name' not in homework:
        raise KeyError(f'Ключ "homework_name" в {homework} не найден ')
    homework_name = homework.get('homework_name')
    if 'status' not in homework:
        raise KeyError(f'Ключ "status" в {homework} не найден')
    homework_status = homework.get('status')
    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES.get(homework_status)
    if homework_status is None or homework_name is None:
        raise KeyError(
            f'В ответе API не найдены "homework_status" и "homework_name"')
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    print(message)
    return message


def check_tokens():
    """Проверяет доступность переменных окружения, 
    которые необходимы для работы программы. 
    Если отсутствует хотя бы одна переменная окружения — 
    функция должна вернуть False, иначе — True.
    """
    logging.info(f'Проверка переменных окружения')
    if PRACTICUM_TOKEN and TELEGRAM_CHAT_ID and TELEGRAM_TOKEN is not None:
        logger.info(f'Все переменные доступны')
        return True
    logging.critical(f'НЕТ КАКОЙ ТО ПЕРЕМЕННОЙ')
    return False


def main():
    """В ней описана основная логика работы программы. 
    Все остальные функции должны запускаться из неё. 
    Последовательность действий должна быть примерно такой:
    Сделать запрос к API.
    Проверить ответ.
    Если есть обновления — получить статус работы из обновления и отправить сообщение в Telegram.
    Подождать некоторое время и сделать новый запрос.
    """
    logging.info(f'Запуск main функции, хоспадиспаси')
    if check_tokens() == False:
        logger.critical(
            f'Нет одной из переменных окружения.\nПрограмма остановлена')
        raise exceptions.MissingVariable(
            f'Нет одной из переменных окружения.\nПрограмма остановлена')

    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        logger.info(f'Соединение с ботом установлено')
    except telegram.error.InvalidToken as error:
        logger.critical(f'Токен бота неверен {error}')
        raise telegram.error.InvalidToken

    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp - RETRY_TIME)
            homeworks_list = check_response(response)
            if homeworks_list != None:
                homework = homeworks_list[0]
                message = parse_status(homework)
                send_message(bot, message)
            else:
                logger.debug(f'Статус домашки не изменился')
            current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
