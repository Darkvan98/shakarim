import os

from dotenv import load_dotenv

load_dotenv()  # backend/.env

# Пример для PostgreSQL:
#   postgresql+psycopg://postgres:postgres@localhost:5432/shakarim_sport
# По умолчанию — SQLite (работает без установки сервера).
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/shakarim_sport",
)

# Токен для доступа к админ-панели (смените в продакшене через переменную окружения)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "shakarim-admin")

OPEN_HOUR = 8    # 08:00
CLOSE_HOUR = 22  # 22:00
MAX_DAYS_AHEAD = 30

# Наценка в выходные (сб/вс)
WEEKEND_MULTIPLIER = 1.2
