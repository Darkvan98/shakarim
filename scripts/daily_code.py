# -*- coding: utf-8 -*-
"""
Показывает сегодняшний (или любой указанной даты) код дня для входа в админку.

Использование:
    python scripts/daily_code.py                      # код на сегодня (секрет по умолчанию)
    python scripts/daily_code.py --secret ВАШ_СЕКРЕТ  # если ADMIN_DAILY_SECRET задан на Vercel
    python scripts/daily_code.py --date 2026-09-29    # код на конкретную дату
"""
import argparse
import hashlib
import hmac
import sys
from datetime import date

sys.path.insert(0, ".")
from backend.app.config import ADMIN_DAILY_SECRET  # noqa: E402


def daily_code(secret: str, d: date) -> str:
    digest = hmac.new(secret.encode(), d.isoformat().encode(), hashlib.sha256).hexdigest()
    digits = "".join(ch for ch in digest if ch.isdigit())
    return (digits + "000000")[:6]


def main():
    parser = argparse.ArgumentParser(description="Код дня для админ-панели Shakarim Sport")
    parser.add_argument("--secret", default=ADMIN_DAILY_SECRET, help="ADMIN_DAILY_SECRET (по умолчанию — из config)")
    parser.add_argument("--date", default=None, help="Дата в формате YYYY-MM-DD (по умолчанию — сегодня)")
    args = parser.parse_args()

    d = date.fromisoformat(args.date) if args.date else date.today()
    print(daily_code(args.secret, d))


if __name__ == "__main__":
    main()
