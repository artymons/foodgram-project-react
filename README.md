![example workflow](https://github.com/artymons/foodgram-project-react/actions/workflows/yamdb_workflow.yml/badge.svg)

# Продуктовый помощник

Foodgram - социальная сеть для публикации рецептов. Сайт выполнен на основе django rest framework и react. В Foodgram реализована функция подписки на авторов, добавление рецептов в избранное, ингредиенты в список покупок, скачивать список покупок

## Для использования сайта перейдите по ссылке http://158.160.48.13/
Для доступа к админке

http://158.160.48.13/admin

Логин: test@ya.ru
Пароль test

# Для локального запуска


Перейдите в папку /infra/

```bash
cd infra/
```

Заполните .env файлы. Например:

```
DB_ENGINE=django.db.backends.postgresql # указываем, что работаем с postgresql
DB_NAME=yamd # имя базы данных
POSTGRES_USER=yamd # логин для подключения к базе данных
POSTGRES_PASSWORD=123456 # пароль для подключения к БД (установите свой)
DB_HOST=db # название сервиса (контейнера)
DB_PORT=5432 # порт для подключения к БД
```


Выполните команды

```bash
docker-compose up -d --build
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py makemigrations users
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --no-input
```

перейдите http://localhost/