Foodgram – Продуктовый помощник

Foodgram — это веб-сервис, позволяющий пользователям публиковать рецепты, добавлять рецепты в избранное и формировать список покупок по выбранным рецептам.

Стек технологий

Backend:
	•	Python 3.9
	•	Django
	•	Django REST Framework (DRF)
	•	Djoser – для управления аутентификацией через DRF
	•	PostgreSQL
	•	Gunicorn
	•	Docker / Docker Compose

Frontend:
	•	React (собирается отдельно и монтируется в Nginx)

DevOps:
	•	Nginx
	•	Docker Compose
	•	GitHub Actions (CI/CD)

Установка и запуск на macOS (или любой системе с Docker)

Убедитесь, что у вас установлены Docker и Docker Compose. Для macOS вы можете использовать Docker Desktop.

1. Клонируйте репозиторий:
git clone https://github.com/disciplina666/foodgram.git

2. Создайте .env файл с настройками:
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=food_db
DB_PORT=5432

DJANGO_SECRET_KEY=your_secret_key
DEBUG=False
ALLOWED_HOSTS=localhost 127.0.0.1 [::1] domain.com(твой домен)

3. Соберите и запустите контейнеры:
docker compose -f docker-compose.production.yml up --build

4. Примените миграции, соберите статику, создайте суперпользователя:
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend python manage.py createsuperuser

5. Структура проекта
.
├── backend/               # Django-приложение
├── frontend/              # React-приложение (только сборка)
├── gateway/               # Nginx конфигурация
├── docker-compose.production.yml
└── README.md
