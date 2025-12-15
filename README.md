# Резюме + вишлист

Простой сайт-резюме на FastAPI с админкой для вишлиста и заметок. Данные резюме лежат в `data/resume.yaml`, фото — в `data/my_photo.jpg`. Сервер стартует одной командой через `uv`.

## Запуск
1. Установите [uv](https://docs.astral.sh/uv/) (если ещё нет): `pip install uv`.
2. Синхронизируйте зависимости: `uv sync`.
3. Задайте токен админа (минимум на время работы):
   ```bash
   echo 'APP_ADMIN_TOKEN=super-secret-token' > .env
   ```
4. Старт сервера:
   ```bash
   uv run start
   ```
   По умолчанию поднимется на `http://127.0.0.1:8000`. Для авто‑перезапуска в разработке есть скрипт: `uv run dev`.

## Docker
Сборка:
```bash
docker build -t resume .
```
Запуск (с сохранением данных/БД на хосте):
```bash
docker run --rm -p 8000:8000 --env-file .env -v "$PWD/data:/app/data" resume
```

### Docker Compose
1) Создайте `.env` (можно начать с `.env.example`): укажите `APP_ADMIN_TOKEN`, при желании поменяйте `DATA_DIR` на путь на хосте.  
2) Запуск/обновление:  
```bash
docker compose up -d --build
```
Сервис поднимется на `${APP_PORT:-8000}`, данные/БД лежат в `${DATA_DIR:-./data}` на хосте.

Настройки через переменные окружения (файл `.env`):
- `APP_ADMIN_TOKEN` — обязателен для админских запросов (заголовок `X-Admin-Token`).
- `APP_HOST`, `APP_PORT` — сетевые параметры (по умолчанию `0.0.0.0:8000`).
- `APP_DATABASE_URL` — путь к БД (по умолчанию SQLite `data/app.db`).
- `APP_DATA_DIR` — путь к каталогу с данными/фото/резюме.
- `APP_TRUSTED_HOSTS` — `*` или список через запятую для доверенных прокси (для `X-Forwarded-*`).

## Структура
- `src/app/__main__.py` — точка входа (`uv run start`).
- `src/app/app_factory.py` — конфигурация FastAPI, маршруты, темплейтинг.
- `src/app/models.py`, `src/app/schemas.py` — модели SQLModel и Pydantic.
- `src/app/static/` и `src/app/templates/` — фронт (чистый HTML/CSS/JS).
- `data/resume.yaml` — резюме и проекты; `data/my_photo.jpg` — фото.
- `data/app.db` — SQLite с вишлистом и постами (создаётся автоматически).

## Как обновлять контент
- **Резюме** — правьте `data/resume.yaml` (новые секции, опыт, навыки). Файл перечитывается на лету.
- **Вишлист** — удобная страница `/wishlist` с фильтрами, бронью и админкой (токен). Добавление поддерживает фото (формат `image/*` хранится в `data/wishlist`).
- **Посты и вишлист** — через админ-блок на главной или через API.
  - Заголовок токена хранится в браузере (LocalStorage). Заголовок: `X-Admin-Token`.
  - API:  
    - `GET /api/resume` — резюме + вишлист + посты.  
    - `GET /api/wishlist` — список пожеланий.  
    - `POST /api/wishlist` (admin) — создать.  
    - `PUT /api/wishlist/{id}` (admin) — обновить.  
    - `DELETE /api/wishlist/{id}` (admin) — удалить.  
    - `POST /api/wishlist/{id}/reserve` — бронь подарка (имя/контакт).  
    - `POST /api/wishlist/{id}/release` (admin) — снять бронь.  
    - `GET /api/posts` — список заметок.  
    - `POST /api/posts` (admin) — создать.  
    - `PUT /api/posts/{id}` (admin), `DELETE /api/posts/{id}` (admin).  

## Что сделано
- Адаптивный лэндинг с разделами «Обо мне», навыки, проекты, опыт, образование, достижения.
- Вишлист отдельной вкладкой `/wishlist` + превью на главной, бронирование без регистрации.
- Админка с токеном в браузере: создание/правка/удаление пунктов, загрузка фото подарков, снятие брони.
- Публикация постов/заметок, простая сетка карточек.
- Данные резюме в отдельном YAML — можно расширять без правок кода.
