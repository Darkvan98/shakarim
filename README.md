# Shakarim Sport — сайт аренды спорткомплекса

Веб-приложение для онлайн-бронирования спортивных залов Shakarim University (г. Семей).

**Стек:** Vue 3 + Vite + vue-router (фронтенд) · FastAPI + SQLAlchemy + PostgreSQL 17 (бэкенд)

## Структура

```
backend/          # FastAPI: API залов, слотов, броней, админка
  app/main.py     # все эндпоинты + сид-данные залов
  app/models.py   # модели Venue / Booking
  app/config.py   # часы работы, админ-токен, цены
frontend/         # Vue 3 SPA
  src/pages/      # Главная, Залы и цены, Бронирование, Моя бронь, Админка
  public/images/  # фото залов и галерея
```

## Быстрый старт

### 1. Бэкенд

```bash
cd backend
python -m venv ../.venv
../.venv/Scripts/pip install -r requirements.txt   # Windows
# ../.venv/bin/pip install -r requirements.txt     # Linux/macOS
../.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### База данных

По умолчанию используется **PostgreSQL**: подключение задаётся в `backend/.env`:

```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/shakarim_sport
ADMIN_TOKEN=shakarim-admin
```

На машине установлен PostgreSQL 17 (служба Windows `postgresql-x64-17`, пароль
`postgres`). БД `shakarim_sport` и все таблицы создаются автоматически при первом
запуске сервера; залы засеиваются сами.

Если PostgreSQL недоступен, можно переключиться на SQLite одной строкой в `backend/.env`:

```
DATABASE_URL=sqlite:///./sport.db
```

### 2. Фронтенд (режим разработки)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, /api проксируется на :8000
```

### Продакшен-вариант одним сервером

```bash
cd frontend && npm run build   # соберёт dist/
# затем просто запустите uvicorn — он отдаст SPA и статику с :8000
```

## Страницы

| URL | Описание |
|---|---|
| `/` | Главная: hero, залы, шаги, галерея с лайтбоксом |
| `/venues` | Залы и цены + занятость на выбранную дату |
| `/booking` | Онлайн-бронирование с выбором свободного слота |
| `/booking/:code` | Проверка брони по коду (например `SK-EBA84C`) |
| `/admin` | Админ-панель: статистика, подтверждение/отмена/удаление броней |

## Админка

Токен задаётся в `backend/.env` (`ADMIN_TOKEN=shakarim-admin`) или переменной окружения:

```bash
set ADMIN_TOKEN=мой-секрет   # Windows
export ADMIN_TOKEN=мой-секрет  # Linux/macOS
```

## API (основное)

- `GET /api/venues` — список залов
- `GET /api/bookings/occupied?venue_id=1&date=YYYY-MM-DD` — занятые слоты
- `POST /api/bookings` — создать бронь (409, если слот занят)
- `GET /api/bookings/{code}` — бронь по коду
- `GET/PATCH/DELETE /api/admin/...` — админ-эндпоинты (заголовок `X-Admin-Token`)

## Настройки

В `backend/app/config.py`: часы работы (08–22), горизонт бронирования (30 дней), цены
будни/выходные задаются на каждый зал в сид-данных `main.py`.
