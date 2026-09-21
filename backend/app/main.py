import json
import os
import re
import shutil
import unicodedata
import uuid
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models
from .config import ADMIN_TOKEN, CLOSE_HOUR, MAX_DAYS_AHEAD, OPEN_HOUR, WEEKEND_MULTIPLIER
from .database import Base, engine, get_db

app = FastAPI(title="Shakarim Sport API", version="1.0.0")

_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
_env_origins = os.environ.get("ALLOWED_ORIGINS", "")
_origins = _default_origins + [o.strip() for o in _env_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api")


# ---------- Schemas ----------

class VenueOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    capacity: int
    area_m2: int
    image: str
    features: list[str]
    price_weekday: int
    price_weekend: int


class BookingCreate(BaseModel):
    venue_id: int
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    hours: int = Field(ge=1, le=6)

    customer_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=6, max_length=30)
    comment: str = Field(default="", max_length=500)


class BookingOut(BaseModel):
    id: int
    code: str
    venue_id: int
    venue_name: str
    date: str
    start_time: str
    end_time: str
    hours: int
    total_price: int
    customer_name: str
    phone: str
    comment: str
    status: str
    created_at: datetime


class BookingStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: str) -> str:
        allowed = {"pending", "confirmed", "cancelled"}
        if v not in allowed:
            raise ValueError(f"Статус должен быть один из: {', '.join(allowed)}")
        return v


class OccupiedSlot(BaseModel):
    start_time: str
    end_time: str
    status: str


class VenuePayload(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    capacity: int = Field(default=0, ge=0, le=10000)
    area_m2: int = Field(default=0, ge=0, le=100000)
    image: str = Field(default="", max_length=300)
    features: list[str] = []
    price_weekday: int = Field(ge=0, le=10_000_000)
    price_weekend: int = Field(ge=0, le=10_000_000)
    sort_order: int = Field(default=0, ge=0, le=1000)


class UploadOut(BaseModel):
    path: str


# ---------- Helpers ----------

def to_venue_out(v: models.Venue) -> VenueOut:
    import json

    return VenueOut(
        id=v.id,
        slug=v.slug,
        name=v.name,
        description=v.description,
        capacity=v.capacity,
        area_m2=v.area_m2,
        image=v.image,
        features=json.loads(v.features) if v.features else [],
        price_weekday=v.price_weekday,
        price_weekend=v.price_weekend,
    )


def to_booking_out(b: models.Booking) -> BookingOut:
    return BookingOut(
        id=b.id,
        code=b.code,
        venue_id=b.venue_id,
        venue_name=b.venue.name,
        date=b.date,
        start_time=b.start_time,
        end_time=b.end_time,
        hours=b.hours,
        total_price=b.total_price,
        customer_name=b.customer_name,
        phone=b.phone,
        comment=b.comment,
        status=b.status,
        created_at=b.created_at,
    )


def validate_date(date_str: str) -> date:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(422, "Некорректная дата, нужен формат YYYY-MM-DD")
    if d < date.today():
        raise HTTPException(422, "Нельзя бронировать на прошедшую дату")
    if d > date.today() + timedelta(days=MAX_DAYS_AHEAD):
        raise HTTPException(422, f"Бронирование доступно максимум на {MAX_DAYS_AHEAD} дней вперёд")
    return d


def parse_hm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def minutes_to_hm(total: int) -> str:
    return f"{total // 60:02d}:{total % 60:02d}"


def venue_price_per_hour(v: models.Venue, d: date) -> int:
    return v.price_weekend if d.weekday() >= 5 else v.price_weekday


def check_overlap(db: Session, venue_id: int, date_str: str, start_min: int, end_min: int,
                  exclude_booking_id: int | None = None) -> models.Booking | None:
    """Возвращает пересекающуюся бронь, если есть (pending и confirmed блокируют слот)."""
    stmt = select(models.Booking).where(
        models.Booking.venue_id == venue_id,
        models.Booking.date == date_str,
        models.Booking.status.in_(["pending", "confirmed"]),
    )
    if exclude_booking_id:
        stmt = stmt.where(models.Booking.id != exclude_booking_id)
    for b in db.scalars(stmt):
        b_start = parse_hm(b.start_time)
        b_end = parse_hm(b.end_time)
        if start_min < b_end and end_min > b_start:
            return b
    return None


# ---------- Public endpoints ----------

@router.get("/venues", response_model=list[VenueOut])
def list_venues(db: Session = Depends(get_db)):
    venues = db.scalars(select(models.Venue).order_by(models.Venue.sort_order)).all()
    return [to_venue_out(v) for v in venues]


@router.get("/venues/{slug}", response_model=VenueOut)
def get_venue(slug: str, db: Session = Depends(get_db)):
    v = db.scalar(select(models.Venue).where(models.Venue.slug == slug))
    if not v:
        raise HTTPException(404, "Зал не найден")
    return to_venue_out(v)


@router.get("/bookings/occupied", response_model=list[OccupiedSlot])
def occupied_slots(
    venue_id: int = Query(...),
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
):
    """Занятые слоты зала на дату (pending + confirmed)."""
    stmt = select(models.Booking).where(
        models.Booking.venue_id == venue_id,
        models.Booking.date == date,
        models.Booking.status.in_(["pending", "confirmed"]),
    )
    return [
        OccupiedSlot(start_time=b.start_time, end_time=b.end_time, status=b.status)
        for b in db.scalars(stmt)
    ]


@router.post("/bookings", response_model=BookingOut, status_code=201)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    d = validate_date(payload.date)

    venue = db.get(models.Venue, payload.venue_id)
    if not venue:
        raise HTTPException(404, "Зал не найден")

    start_min = parse_hm(payload.start_time)
    end_min = start_min + payload.hours * 60
    if start_min < OPEN_HOUR * 60 or end_min > CLOSE_HOUR * 60:
        raise HTTPException(422, f"Часы работы: {OPEN_HOUR}:00–{CLOSE_HOUR}:00")

    if check_overlap(db, venue.id, payload.date, start_min, end_min):
        raise HTTPException(409, "Этот слот уже занят. Выберите другое время.")

    price_per_hour = venue_price_per_hour(venue, d)
    total = price_per_hour * payload.hours

    booking = models.Booking(
        code=generate_code(),
        venue_id=venue.id,
        date=payload.date,
        start_time=minutes_to_hm(start_min),
        end_time=minutes_to_hm(end_min),
        hours=payload.hours,
        total_price=total,
        customer_name=payload.customer_name.strip(),
        phone=payload.phone.strip(),
        comment=payload.comment.strip(),
        status="pending",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return to_booking_out(booking)


@router.get("/bookings/{code}", response_model=BookingOut)
def get_booking(code: str, db: Session = Depends(get_db)):
    b = db.scalar(select(models.Booking).where(models.Booking.code == code))
    if not b:
        raise HTTPException(404, "Бронирование не найдено")
    return to_booking_out(b)


def generate_code() -> str:
    import secrets

    return f"SK-{secrets.token_hex(3).upper()}"


# ---------- Admin endpoints ----------

def require_admin(x_admin_token: str = Header(default="")):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(401, "Неверный админ-токен")


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def make_slug(name: str, db: Session, exclude_id: int | None = None) -> str:
    """Транслит названия в slug, уникальный среди залов."""
    ru = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "",
        "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    s = "".join(ru.get(ch, ch) for ch in name.lower())
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60] or "venue"
    base, n = s, 2
    stmt = select(models.Venue.id, models.Venue.slug)
    taken = {
        slug for vid, slug in db.execute(stmt)
        if exclude_id is None or vid != exclude_id
    }
    while s in taken:
        s = f"{base}-{n}"
        n += 1
    return s


UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "public", "images", "uploads"
)
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _save_upload(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(422, "Только изображения: " + ", ".join(sorted(ALLOWED_IMAGE_EXT)))
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    fname = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, fname), "wb") as f:
        shutil.copyfileobj(file.file, f)
    return f"/images/uploads/{fname}"


@router.get("/admin/venues", response_model=list[VenueOut])
def admin_list_venues(db: Session = Depends(get_db), _: None = Depends(require_admin)):
    venues = db.scalars(select(models.Venue).order_by(models.Venue.sort_order)).all()
    return [to_venue_out(v) for v in venues]


@router.post("/admin/venues", response_model=VenueOut, status_code=201)
def admin_create_venue(payload: VenuePayload, db: Session = Depends(get_db), _: None = Depends(require_admin)):
    venue = models.Venue(
        slug=make_slug(payload.name, db),
        **payload.model_dump(exclude={"features"}),
        features=json.dumps(payload.features, ensure_ascii=False),
    )
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return to_venue_out(venue)


@router.patch("/admin/venues/{venue_id}", response_model=VenueOut)
def admin_update_venue(
    venue_id: int,
    payload: VenuePayload,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    venue = db.get(models.Venue, venue_id)
    if not venue:
        raise HTTPException(404, "Зал не найден")
    data = payload.model_dump(exclude={"features"})
    for key, value in data.items():
        setattr(venue, key, value)
    venue.features = json.dumps(payload.features, ensure_ascii=False)
    db.commit()
    db.refresh(venue)
    return to_venue_out(venue)


@router.delete("/admin/venues/{venue_id}", status_code=204)
def admin_delete_venue(venue_id: int, db: Session = Depends(get_db), _: None = Depends(require_admin)):
    venue = db.get(models.Venue, venue_id)
    if not venue:
        raise HTTPException(404, "Зал не найден")
    has_bookings = db.scalar(
        select(func.count(models.Booking.id)).where(models.Booking.venue_id == venue_id)
    )
    if has_bookings:
        raise HTTPException(409, "У зала есть брони — сначала удалите их")
    db.delete(venue)
    db.commit()


@router.post("/admin/uploads", response_model=UploadOut, status_code=201)
def admin_upload_image(
    file: UploadFile = File(...),
    _: None = Depends(require_admin),
):
    return UploadOut(path=_save_upload(file))


@router.get("/admin/bookings", response_model=list[BookingOut])
def admin_list_bookings(
    status: str | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    stmt = select(models.Booking).order_by(models.Booking.created_at.desc())
    if status:
        stmt = stmt.where(models.Booking.status == status)
    return [to_booking_out(b) for b in db.scalars(stmt)]


@router.get("/admin/stats")
def admin_stats(db: Session = Depends(get_db), _: None = Depends(require_admin)):
    total = db.scalar(select(func.count(models.Booking.id))) or 0
    pending = db.scalar(
        select(func.count(models.Booking.id)).where(models.Booking.status == "pending")
    ) or 0
    confirmed = db.scalar(
        select(func.count(models.Booking.id)).where(models.Booking.status == "confirmed")
    ) or 0
    revenue = db.scalar(
        select(func.coalesce(func.sum(models.Booking.total_price), 0)).where(
            models.Booking.status.in_(["pending", "confirmed"])
        )
    ) or 0
    return {
        "total": total,
        "pending": pending,
        "confirmed": confirmed,
        "revenue": revenue,
    }


@router.patch("/admin/bookings/{booking_id}/status", response_model=BookingOut)
def admin_update_status(
    booking_id: int,
    payload: BookingStatusUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    b = db.get(models.Booking, booking_id)
    if not b:
        raise HTTPException(404, "Бронирование не найдено")

    if payload.status == "confirmed":
        start_min = parse_hm(b.start_time)
        end_min = parse_hm(b.end_time)
        overlap = check_overlap(db, b.venue_id, b.date, start_min, end_min,
                                exclude_booking_id=b.id)
        if overlap:
            raise HTTPException(409, "Конфликт: на это время уже есть подтверждённая бронь")

    b.status = payload.status
    db.commit()
    db.refresh(b)
    return to_booking_out(b)


@router.delete("/admin/bookings/{booking_id}", status_code=204)
def admin_delete_booking(booking_id: int, db: Session = Depends(get_db), _: None = Depends(require_admin)):
    b = db.get(models.Booking, booking_id)
    if not b:
        raise HTTPException(404, "Бронирование не найдено")
    db.delete(b)
    db.commit()


app.include_router(router)

# ---------- DB init (lazy, для совместимости с serverless) ----------

_db_initialized = False


def _ensure_db():
    """Создаёт таблицы и seed-данные при первом запросе (serverless-safe)."""
    global _db_initialized
    if _db_initialized:
        return
    Base.metadata.create_all(engine)
    import json

    from .database import SessionLocal

    db = SessionLocal()
    try:
        if db.scalar(select(func.count(models.Venue.id))):
            _db_initialized = True
            return
        venues = [
            models.Venue(
                slug="universal-hall",
                name="Универсальный игровой зал",
                description=(
                    "Просторный зал с профессиональным покрытием для волейбола, "
                    "баскетбола, мини-футбола и бадминтона. Трибуны, раздевалки, душевые."
                ),
                capacity=60,
                area_m2=900,
                image="/images/hall-universal.jpeg",
                features=json.dumps(
                    ["Волейбол", "Баскетбол", "Мини-футбол", "Бадминтон", "Трибуны", "Раздевалки"],
                    ensure_ascii=False,
                ),
                price_weekday=15000,
                price_weekend=18000,
                sort_order=1,
            ),
            models.Venue(
                slug="small-hall",
                name="Малый игровой зал",
                description=(
                    "Уютный зал для тренировок небольших групп: волейбол, бадминтон, "
                    "общая физическая подготовка, секции и детские группы."
                ),
                capacity=30,
                area_m2=450,
                image="/images/hall-small.jpeg",
                features=json.dumps(
                    ["Волейбол", "Бадминтон", "Секции", "Детские группы", "Тёплое освещение"],
                    ensure_ascii=False,
                ),
                price_weekday=9000,
                price_weekend=11000,
                sort_order=2,
            ),
            models.Venue(
                slug="gym",
                name="Тренажёрный зал",
                description=(
                    "Кардио-зона (беговые дорожки, велотренажёры), свободные веса, "
                    "силовые станции. Для групповых и персональных тренировок."
                ),
                capacity=25,
                area_m2=400,
                image="/images/hall-gym.jpeg",
                features=json.dumps(
                    ["Кардио-зона", "Свободные веса", "Силовые станции", "Персональные тренировки"],
                    ensure_ascii=False,
                ),
                price_weekday=8000,
                price_weekend=10000,
                sort_order=3,
            ),
        ]
        db.add_all(venues)
        db.commit()
        _db_initialized = True
    finally:
        db.close()


@app.middleware("http")
async def ensure_db_middleware(request, call_next):
    """Гарантирует инициализацию БД перед обработкой запроса."""
    _ensure_db()
    return await call_next(request)

