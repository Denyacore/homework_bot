import json
import logging
import os
import sys
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

import exceptions

logger = logging.getLogger(__name__)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    logging.info('Отправляем сообщение в telegramm')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError:
        raise telegram.error.TelegramError('Сообщение не отправлено')
    else:
        logger.info(f'Отправлено сообщение с текстом: {message}')


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра функция получает временную метку.
    В случае успешного запроса должна вернуть ответ API,
    преобразовав его из формата JSON к типам данных Python.
    """
    logging.info('Отпрравляем запрос к API и получаем ответ')
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    request_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params,
    }
    try:
        response = requests.get(**request_params)
        logger.info(f'Отправлен запрос к API'
                    f'\nКод ответа {response.status_code}')
        if response.status_code != HTTPStatus.OK:
            logger.error('Что то с API')
            raise exceptions.ServerError(
                f'Ошибка ответа API:'
                f'{response.status_code},'
                f'{response.headers},'
                f'{response.text},'
            )
    except requests.exceptions.RequestException as error:
        message = f'Эндпойнт недоступен: {error}'
        logger.error(message)
        raise requests.exceptions.RequestException(message)
    except json.decoder.JSONDecodeError as error:
        raise Exception((f'Ответ {response.text} получен не в виде JSON: '
                         f'{error}'))
    except Exception:
        raise Exception('Неизвестная ошибка')
    answer_api = response.json()
    answer_api_succsess = (
        f'Получен ответ API с типом данных {type(answer_api)}'
    )
    logger.info(answer_api_succsess)
    return answer_api


def check_response(answer_api):
    """Проверяет ответ API на корректность.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    Если ответ API соответствует ожиданиям,
    то функция должна вернуть список домашних работ (он может быть и пустым),
    доступный в ответе API по ключу 'homeworks'.
    """
    logging.info('Проверяем корректность ответа API')
    if isinstance(answer_api, dict):
        try:
            homework_list = (answer_api['homeworks'])
            logger.info(f'Получен список домашек типа {type(homework_list)}')
        except KeyError as error:
            logger.error(f'В ответе не обнаружен ключ {error}')
            raise exceptions.KeyNotFound(f'В ответе не обнаружен ключ {error}')
        homework = homework_list[0]
        logger.info(f'Получена домашка для доработки типа {type(homework)}')
        return homework
    else:
        raise TypeError('Ответ API не содержит словарь')


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра
    функция получает только один элемент из списка домашних работ.
    В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку,
    содержащую один из вердиктов словаря VERDICTS.
    """
    logging.info('Извлекаем статус и имя домашки')
    if homework is None:
        raise exceptions.HomeworkNoneError('Домашнаяя работа отсутствует')
    if 'homework_name' not in homework:
        raise KeyError(f'Ключ "homework_name" в {homework} не найден ')
    homework_name = homework.get('homework_name')
    if 'status' not in homework:
        raise KeyError(f'Ключ "status" в {homework} не найден')
    homework_status = homework.get('status')
    if homework_status in VERDICTS:
        verdict = VERDICTS.get(homework_status)
    if homework_status is None or homework_name is None:
        raise KeyError(
            'В ответе API не найдены "homework_status" и "homework_name"')
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    return message


def check_tokens():
    """Проверяет доступность переменных окружения."""
    logging.info('Проверка переменных окружения')
    if PRACTICUM_TOKEN and TELEGRAM_CHAT_ID and TELEGRAM_TOKEN is not None:
        logger.info('Все переменные доступны')
        return True
    logging.critical('НЕТ КАКОЙ ТО ПЕРЕМЕННОЙ')
    return False


def main():
    """В ней описана основная логика работы программы.
    Все остальные функции должны запускаться из неё.
    Последовательность действий должна быть примерно такой:
    Сделать запрос к API.
    Проверить ответ.
    Если есть обновления — получить статус работы из обновления
    и отправить сообщение в Telegram.
    Подождать некоторое время и сделать новый запрос.
    """
    logging.info('Запуск main функции, хоспадиспаси')
    if check_tokens() is False:
        logger.critical(
            'Нет одной из переменных окружения.\nПрограмма остановлена')
        raise exceptions.MissingVariable(
            'Нет одной из переменных окружения.\nПрограмма остановлена')

    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        logger.info('Соединение с ботом установлено')
    except telegram.error.InvalidToken as error:
        logger.critical(f'Токен бота неверен {error}')
        raise telegram.error.InvalidToken

    current_timestamp = 1549962000
    current_report = {}
    prev_report = {}
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            current_report[response.get(
                'homework_name')] = response.get('name')
            if current_report != prev_report:
                send_message(bot, message)
                prev_report = current_report.copy()
            current_report[response.get(
                'homework_name')] = response.get('name')
            current_timestamp = response.get('current_date')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    try:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s, %(levelname)s, %(message)s, %(name)s, %(lineno)d'
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler = RotatingFileHandler('main.log',
                                      maxBytes=50000000,
                                      backupCount=5,
                                      encoding='UTF-8'
                                      )
        logger.addHandler(handler)
        main()
    except KeyboardInterrupt:
        sys.exit()
