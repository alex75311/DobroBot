# DobroBot VK
Чат-бот ВК для проекта [Добро mail.ru](dobro.mail.ru)

### Установка зависимостей:
```pip install -r requirements.txt```

### Развернуть сервер ML
https://github.com/fogugy/dobro_ml

### Установить свои данные в файле conf.py или в переменных окружения

```
BOT_TOKEN = 'ТОКЕН_БОТА'
USER_TOKEN = 'ТОКЕН_АДМИНИСТРАТОРА_ГРУППЫ'
API_APP = '0'
API_KEY = '0'
GROUP_ID = ID группы ВК
ALBOM_ID = ID альбама для загрузки фото
URL_RSS = 'https://dobro.mail.ru/projects/rss/target/'
PREDICTOR_URL = 'ХОСТ_ML'
DB_NAME = 'ИМЯ_БД_POSTGRES'
DB_USER = 'ПОЛЬЗОВАТЕЛЬ_БД'
DB_PASSWORD = 'ПАРОЛЬ_БД'
DB_IP = 'IP_БД'
DB_PORT = 'ПОРТ_БД'
```

### Запуск:
```models.py``` - запустить для создания таблиц в БД

```parser.py``` - запускать по расписанию для обновления проектов.

```dobrobot.py``` - запустить бота

### Запуск в контейнере
Установить ```docker-compose```

```apt install docker-compose```

Скачать репозитории

```git clone https://github.com/alex75311/DobroBot.git```

```git clone https://github.com/fogugy/dobro_ml.git```

```cd DobroBot/```

В файле ```docker-compose``` изменить данные на свои

```
BOT_TOKEN:
USER_TOKEN:
GROUP_ID:
ALBOM_ID:
API_APP:
API_KEY:
PREDICTOR_URL:
DB_NAME:
DB_USER:
DB_PASSWORD:
DB_IP:
DB_PORT:
```

Выполнить команду ```docker-compose up -d``` 

При запуске контейнеров, автоматически создается БД (если не была создана ранее) 
и запускается обновление проектов, что занимает около 5-8 минут, только после этого бот начинает
отвечать на запросы.
