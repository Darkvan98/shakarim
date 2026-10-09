"""Парсинг вставленной таблицы расписания занятости (Excel / Word / текст).

Поддерживаемые форматы строк (одна строка = одна запись):
    12.10          09:00  11:00   Секция по волейболу
    12.10.2026     9:00-11:00     Секция
    Пн 12.10       09:00 – 11:00  Секция
    2026-10-12; 09:00; 11:00; Секция
    Вторник        14:00  15:30   Тренировка   (дата = ближайший такой день недели на неделе импорта)

Разделители: табы, 2+ пробела, точка с запятой, пайп, длинное тире между временами.
Импорт идёт на неделю, начинающуюся с week_start (YYYY-MM-DD).
"""

import datetime as _dt
import re as _re

MONTHS_RU = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}
WEEKDAYS_RU = {
    "понедельник": 0, "вторник": 1, "среда": 2, "четверг": 3,
    "пятница": 4, "суббота": 5, "воскресенье": 6,
    "пн": 0, "вт": 1, "ср": 2, "чт": 3, "пт": 4, "сб": 5, "вс": 6,
}

_SPLIT_RE = _re.compile(r"\t+|;|\|| {2,}")
_TIME_RE = _re.compile(r"(\d{1,2})[:.:](\d{2})")
_TIME_RANGE_RE = _re.compile(
    r"(\d{1,2}[:.:]\d{2})\s*[–—-]+\s*(?:до\s*)?(\d{1,2}[:.:]\d{2})"
)
_DATE_DMY_RE = _re.compile(r"(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?")
_DATE_ISO_RE = _re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_DATE_WORD_RE = _re.compile(
    r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)",
    _re.IGNORECASE,
)
_WEEKDAY_WORD_RE = _re.compile(
    r"(понедельник|вторник|среда|четверг|пятница|суббота|воскресенье|пн|вт|ср|чт|пт|сб|вс)",
    _re.IGNORECASE,
)


def _parse_time_to_min(s: str) -> int | None:
    m = _TIME_RE.search(s)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 24 or mi > 59:
        return None
    # 24:00 трактуем как конец суток
    return 24 * 60 if h == 24 else h * 60 + mi


def _parse_date(s: str, week_start: _dt.date) -> _dt.date | None:
    s = s.strip().lower()
    m = _DATE_ISO_RE.search(s)
    if m:
        try:
            return _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = _DATE_DMY_RE.search(s)
    if m:
        day, mon = int(m.group(1)), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else week_start.year
        try:
            return _dt.date(year, mon, day)
        except ValueError:
            return None
    m = _DATE_WORD_RE.search(s)
    if m:
        day, mon = int(m.group(1)), MONTHS_RU[m.group(2).lower()]
        try:
            return _dt.date(week_start.year, mon, day)
        except ValueError:
            return None
    m = _WEEKDAY_WORD_RE.search(s)
    if s.strip() in WEEKDAYS_RU or (m and _re.fullmatch(r"[а-яё\s]+", s.strip())):
        wd = WEEKDAYS_RU[s.strip()] if s.strip() in WEEKDAYS_RU else WEEKDAYS_RU[m.group(1).lower()]
        delta = (wd - week_start.weekday()) % 7
        return week_start + _dt.timedelta(days=delta)
    # просто число (день месяца) — привязываем к неделе импорта
    m = _re.fullmatch(r"(\d{1,2})", s)
    if m:
        day = int(m.group(1))
        for off in range(7):
            d = week_start + _dt.timedelta(days=off)
            if d.day == day:
                return d
    return None


def parse_rows(text: str, week_start_str: str, venue_names: list[str] | None = None):
    """Разбирает вставленный текст на записи.

    Поддержаны форматы строк:
    1) Построчный: дата · время начала · время конца · кем занято.
    2) Таблица «день недели × залы»: первая колонка — день, дальше по колонке
       ячейки вида «ПОК 18:10–20:00». Названия колонок сопоставляются со списком
       залов (venue_names); для каждой записи возвращается venue_name.

    Возвращает (записи, ошибки). Запись: {venue_name, date, start_time, end_time, label}.
    """
    try:
        week_start = _dt.date.fromisoformat(week_start_str)
    except ValueError:
        raise ValueError("Некорректная дата начала недели, нужен формат YYYY-MM-DD")

    items: list[dict] = []
    errors: list[str] = []

    # --- Таблица «день недели × залы»? ---
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    header_cols = None
    if venue_names and len(lines) >= 2:
        first = lines[0]
        cols = [p.strip() for p in _SPLIT_RE.split(first) if p.strip()]
        # В шапке нет времени, файлов дат нет
        has_time = bool(_TIME_RE.search(first))
        matches = 0
        if not has_time:
            for c in cols[1:]:
                cl = c.lower().strip()
                for vn in venue_names:
                    vl = vn.lower().strip()
                    if vl and (vl in cl or cl in vl):
                        matches += 1
                        break
        if not has_time and matches >= max(1, len(cols) - 1) // 2:
            header_cols = cols

    if header_cols is not None:
        # Сопоставление колонок с залами
        col_venue: list[str | None] = [None]
        for c in header_cols[1:]:
            cl = c.lower().strip()
            found = None
            for vn in venue_names:
                vl = vn.lower().strip()
                if vl and (vl in cl or cl in vl):
                    found = vn
                    break
            col_venue.append(found)

        for lineno, line in enumerate(lines[1:], start=2):
            parts = [p.strip() for p in _SPLIT_RE.split(line) if p.strip()]
            if not parts:
                continue
            day_raw = parts[0]
            d = _parse_date(day_raw, week_start)
            if d is None:
                errors.append(f"Строка {lineno}: не распознан день «{day_raw[:40]}»")
                continue
            # Ячейки по колонкам; в Excel при вставке пустые колонки могут затираться —
            # сопоставляем по индексу, если частей меньше, чем колонок, с ожидаемым сдвигом
            for idx, vn in enumerate(col_venue[1:], start=1):
                cell = parts[idx] if idx < len(parts) else "—"
                if not vn:
                    continue
                cl = cell.strip()
                if not cl or cl in {"—", "-", "–", "—", ""}:
                    continue
                mr = _TIME_RANGE_RE.search(cl)
                if not mr:
                    errors.append(f"Строка {lineno}, «{header_cols[idx] if idx < len(header_cols) else idx}»: нет времени в «{cl[:40]}»")
                    continue
                ts = _parse_time_to_min(mr.group(1))
                te = _parse_time_to_min(mr.group(2))
                if ts is None or te is None or te <= ts:
                    errors.append(f"Строка {lineno}, «{header_cols[idx] if idx < len(header_cols) else idx}»: некорректное время «{cl[:40]}»")
                    continue
                label = _TIME_RANGE_RE.sub("", cl).strip(" ;|\t–—-. ")
                items.append({
                    "venue_name": vn,
                    "date": d.isoformat(),
                    "start_time": f"{ts // 60:02d}:{ts % 60:02d}",
                    "end_time": f"{te // 60:02d}:{te % 60:02d}",
                    "label": label or "",
                })

        return items, errors

    # --- Построчный формат (дата · от · до · кем) ---
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        # сравнение заголовка таблицы пропускаем
        if _re.search(r"(дата|день|время|занят|кем)", line, _re.IGNORECASE) and not _TIME_RE.search(line):
            continue

        parts = [p.strip() for p in _SPLIT_RE.split(line) if p.strip()]

        dtime_found = _TIME_RANGE_RE.search(line)
        date_str = None
        time_start = time_end = None
        # Диапазон «9:00-11:00» или «09:00 – 11:00»
        if dtime_found:
            time_start = _parse_time_to_min(dtime_found.group(1))
            time_end = _parse_time_to_min(dtime_found.group(2))
            head = line[: dtime_found.start()].strip()
            tail = line[dtime_found.end():].strip()

        # Диапазон Excel: одна ячейка «09:00-11:00» или полностью сплит на три части (дата, от, до)
        if time_start is None or time_end is None:
            # Ячейка с диапазоном среди частей
            for p in parts:
                mr = _TIME_RANGE_RE.search(p)
                if mr:
                    time_start = _parse_time_to_min(mr.group(1))
                    time_end = _parse_time_to_min(mr.group(2))
                    break

        # Раздельные ячейки «от» «до»: нужно минимум 2 временных, одна часть — минимум дата+2 времени
        if (time_start is None or time_end is None) and len(parts) >= 3:
            if time_start is None:
                time_start = _parse_time_to_min(parts[1])
            if time_end is None:
                time_end = _parse_time_to_min(parts[2])
            head = parts[0]
            tail = " ".join(parts[3:]) if len(parts) >= 4 else ""

        if time_start is None or time_end is None:
            errors.append(f"Строка {lineno}: не найдено время в «{line[:60]}»")
            continue

        # дата в левой части
        head_clean = head.strip(" ;|\t")
        label_src = tail
        if head_clean:
            # отрезаем слово дня недели перед датой («Пн 12.10»)
            date_str = head_clean
        if head_clean:
            d = _parse_date(head_clean, week_start)
            if d is None and parts:
                d = _parse_date(parts[0], week_start)
            if d is not None:
                date_val = d
            else:
                errors.append(f"Строка {lineno}: не распознана дата «{head_clean[:40]}»")
                continue
        else:
            errors.append(f"Строка {lineno}: нет даты")
            continue

        if time_start is None or time_end is None or time_end <= time_start:
            errors.append(f"Строка {lineno}: некорректное время в «{line[:60]}»")
            continue

        # label: хвост строки без даты/времени
        label = label_src.strip(" ;|\t–—-")
        # убрать повторы времени из label
        label = _TIME_RANGE_RE.sub("", label)
        label = _re.sub(r"\b\d{1,2}[:.:]\d{2}\b", "", label).strip(" ;|\t–—- ")

        items.append({
            "venue_name": None,
            "date": date_val.isoformat(),
            "start_time": f"{time_start // 60:02d}:{time_start % 60:02d}",
            "end_time": f"{time_end // 60:02d}:{time_end % 60:02d}",
            "label": label or "",
        })

    return items, errors
