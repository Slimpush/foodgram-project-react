[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat-square&logo=gunicorn)](https://gunicorn.org/)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Yandex.Cloud](https://img.shields.io/badge/-Yandex.Cloud-464646?style=flat-square&logo=Yandex.Cloud)](https://cloud.yandex.ru/)

Представляю платформу для публикации рецептов foodgram. Вы можете ознакомиться
с рецептами пользователей или зарегистрироваться и воспользоваться полным функционалом
платформы. Подпиской на авторов, добавлением рецептов в избранное и формированием
корзины для покупок с последующим скачиванием файла с нужными для рецепта ингредиентами.
## Даннйы проект доступен по [домену](http://foodgram.viewdns.net/)

## Подготовка и запуск проекта

## Если вы работаете на удаленном сервере:
* Выполните вход на свой удаленный сервер
* Обновите список доступных пакетов и скачайте curl: 
```
sudo apt update
sudo apt install curl
```
* Проверьте, есль ли на вашем сервере Git и склонируйте репозиторий:
```
git --version 
git clone git@github.com:Slimpush/foodgram-project-react.git
```
* С помощью curl скачайте скрипт для установки docker с оффициального сайте и запустите:
```
curl -fSL https://get.docker.com -o get-docker.sh 
sudo sh ./get-docker.sh
```
* Установите docker-compose на сервер и проверьте что Docker работает:
```
sudo apt-get install docker-compose-plugin 
sudo systemctl status docker 
```
* Локально отредактируйте файл infra/nginx.conf и в строке server_name впишите IP
* Скопируйте файлы nginx.conf и docker-compose.yml из директории infra себе на сервер:
```
scp docker-compose.yml <username>@<host>:/home/<username>/docker-compose.yml
scp nginx.conf <username>@<host>:/home/<username>/nginx.conf
```

* Cоздайте .env файл и впишите:
    ```
    SECRET_KEY=<секретный ключ проекта django>
    DB_ENGINE=<django.db.backends.postgresql>
    DB_NAME=<имя базы данных postgres>
    DB_USER=<пользователь бд>
    DB_PASSWORD=<пароль>
    DB_HOST=<db>
    DB_PORT=<5432>
    ```
* Для работы с Workflow добавьте в Secrets на GitHub переменные окружения для работы:
    ```
    DB_ENGINE=<django.db.backends.postgresql>
    DB_NAME=<имя базы данных postgres>
    DB_USER=<пользователь бд>
    DB_PASSWORD=<пароль>
    DB_HOST=<db>
    DB_PORT=<5432>
    
    DOCKER_PASSWORD=<пароль от DockerHub>
    DOCKER_USERNAME=<имя пользователя>

    USER=<username для подключения к серверу>
    HOST=<IP сервера>
    PASSPHRASE=<пароль для сервера, если он установлен>
    SSH_KEY=<ваш SSH ключ>

    TELEGRAM_TO=<ID чата, в который придет сообщение> (c помощью userinfobot)
    TELEGRAM_TOKEN=<токен вашего бота> (с помощью BotFather)

    Так же можно опционально скрыть эти опции из settings:
    ALLOWED_HOSTS=<ваш_ip>,<127.0.0.1>,<localhost>,<ваш_домен>
    DEBUG=<True/False>
    SECRET_KEY=<секретный ключ проекта django>
    ```
    Проверьте код на соотетствие PEP8 и сделайте Workflow, 
    если всё пройдет удачно - вы получите уведомление в telegram.
    Если что-то не заработает - откройте логи в actions и посмотрите
    в чем причина.
    
  
* На сервере соберите docker-compose:
```
sudo docker-compose up -d --build
```
* После успешной сборки на сервере выполните команды (только после первого деплоя):
    - Соберите статические файлы:
    ```
    sudo docker-compose exec backend python manage.py collectstatic --noinput
    ```
    - Примените миграции:
    ```
    sudo docker-compose exec backend python manage.py makemigrations
    sudo docker-compose exec backend python manage.py migrate
    ```
    - Создать суперпользователя Django:
    ```
    sudo docker-compose exec backend python manage.py createsuperuser
    ```
    - Вы можете предзагрузить ингредиенты в базу данных:  
    *Если файл не указывать, по умолчанию выберется ingredients.json*
    ```
    sudo docker-compose exec backend python manage.py load_ingredients <Название файла из директории data>
    ```
    - Проект будет доступен по вашему IP


