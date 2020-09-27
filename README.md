# DobroBot VK
Чат-бот ВК для проекта [Добро mail.ru](dobro.mail.ru)

### Установка зависимостей:
```pip install -r requirements.txt```

### Развернуть сервер ML
https://github.com/fogugy/dobro_ml

### Необходимо создать файл conf.py следующего содержания

```
BOT_TOKEN = 'ТОКЕН_БОТА'
USER_TOKEN = 'ТОКЕН_АДМИНИСТРАТОРА_ГРУППЫ'
API_APP = '0'
API_KEY = '0'
URL_RSS = 'https://dobro.mail.ru/projects/rss/target/'
PREDICTOR_URL = 'ХОСТ_ML'
DB_NAME = 'ИМЯ_БД_POSTGRES'
DB_USER = 'ПОЛЬЗОВАТЕЛЬ_БД'
DB_PASSWORD = 'ПАРОЛЬ_БД'
DB_IP = 'IP_БД'
DB_PORT = 'ПОРТ_БД'
```

### Запуск:

```parser.py``` - запускать по расписанию для обновления проектов.

```dobrobot.py``` - запустить бота
