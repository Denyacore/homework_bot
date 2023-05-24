# Tg bot for review notifications by [Denyacore](https://github.com/Denyacore)

Бот работает с API Яндекс.Практикум, отслеживает статус последней домашней работы. При его изменении - оповещает.


## Tech Stack

- [Python 3.7](https://www.python.org/)
- [Python-telegram-bot](https://docs.python-telegram-bot.org/en/stable/)


## Authors

- [Denyacore](https://github.com/Denyacore)


## Deployment

To deploy this project run:

1. Clone the repository and go to it on the command line:

```
https://github.com/Denyacore/homework_bot
```

```
cd homework_bot
```

2. Create and activate a virtual environment:

```
python3 -m venv env
        or
py -m venv venv
```

```
source venv/Scripts/activate
```
3. Upgrade installer
```
python3 -m pip install --upgrade pip
                or
py -m pip install --upgrade pip
```

4. Install dependencies from a file *requirements.txt* :

```
pip install -r requirements.txt
```
5. Create a file .env and write in it:
```
PRACTICUM_TOKEN=<PRACTICUM_TOKEN>
TELEGRAM_TOKEN=<TELEGRAM_TOKEN>
CHAT_ID=<CHAT_ID>
```

 PRACTICUM_TOKEN take [here](https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a) and replace <PRACTICUM_TOKEN> in file

 TELEGRAM_TOKEN take [here](https://t.me/BotFather) and replace <TELEGRAM_TOKEN> in file

 CHAT_ID take [here](https://t.me/userinfobot) and replace <CHAT_ID> in file
 

6. Start bot:
```
python homework.py
```
