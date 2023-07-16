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
```
* Из репозитория по адресу https://github.com/Slimpush/foodgram-project-react/infra скопируйте себе файлы nginx.conf и docker-compose.yml
* Скачайте и установите себе Docker по инструкции с оффициального и проверьте что Docker работает:
```
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


