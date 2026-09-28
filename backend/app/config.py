import os

from dotenv import load_dotenv

# Загружаем .env (локальная разработка); на Vercel переменные задаются через Dashboard
load_dotenv()

# ---------- Database ----------
# Neon / Vercel Postgres дают URL вида:
#   postgres://user:pass@host/db?sslmode=require
# SQLAlchemy 2.x нужен драйвер psycopg, поэтому приводим к:
#   postgresql+psycopg://user:pass@host/db?sslmode=require

_raw_db_url = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/shakarim_sport",
)

# Neon/Supabase/Heroku часто отдают "postgres://..." — заменяем на "postgresql+psycopg://..."
if _raw_db_url.startswith("postgres://"):
    DB_URL = _raw_db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif _raw_db_url.startswith("postgresql://"):
    DB_URL = _raw_db_url.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    DB_URL = _raw_db_url

# Токен для доступа к админ-панели (совместимость; новые входы — через логин/пароль)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "shakarim-admin")

# Логин и пароль администратора (смените в продакшене через переменные окружения)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "shakarim2026")

# Секрет для ежедневного кода доступа (код дня). Смените в продакшене.
# Код дня = первые 6 цифр HMAC-SHA256(секрет, дата YYYY-MM-DD) — меняется сам каждую полночь.
ADMIN_DAILY_SECRET = os.getenv("ADMIN_DAILY_SECRET", "shakarim-daily-secret")

OPEN_HOUR = 8    # 08:00
CLOSE_HOUR = 22  # 22:00
MAX_DAYS_AHEAD = 30

# Наценка в выходные (сб/вс)
WEEKEND_MULTIPLIER = 1.2
