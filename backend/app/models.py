from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    sports_complex: Mapped[str] = mapped_column(String, default="")
    description: Mapped[str] = mapped_column(String, default="")
    capacity: Mapped[int] = mapped_column(Integer, default=0)
    area_m2: Mapped[int] = mapped_column(Integer, default=0)
    image: Mapped[str] = mapped_column(String, default="")
    images: Mapped[str] = mapped_column(String, default="")  # JSON-список путей к доп. фото
    features: Mapped[str] = mapped_column(String, default="")  # JSON-список
    price_weekday: Mapped[int] = mapped_column(Integer)  # тг/час, пн-пт
    price_weekend: Mapped[int] = mapped_column(Integer)  # тг/час, сб-вс
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="venue")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"))
    date: Mapped[str] = mapped_column(String, index=True)   # YYYY-MM-DD
    start_time: Mapped[str] = mapped_column(String)          # HH:MM
    end_time: Mapped[str] = mapped_column(String)            # HH:MM
    hours: Mapped[int] = mapped_column(Integer)
    total_price: Mapped[int] = mapped_column(Integer)
    customer_name: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, default="")
    comment: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    venue: Mapped["Venue"] = relationship(back_populates="bookings")


class VenueBlock(Base):
    """Ручная блокировка времени зала администратором (вне системы бронирования):
    когда занято, на сколько и кем."""

    __tablename__ = "venue_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), index=True)
    date: Mapped[str] = mapped_column(String, index=True)   # YYYY-MM-DD
    start_time: Mapped[str] = mapped_column(String)          # HH:MM
    end_time: Mapped[str] = mapped_column(String)            # HH:MM
    label: Mapped[str] = mapped_column(String, default="")   # кем занято
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UploadedImage(Base):
    """Изображения, загруженные через админку.
    Храним в БД: на Vercel файловая система только для чтения."""

    __tablename__ = "uploaded_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String, default="")
    content_type: Mapped[str] = mapped_column(String, default="")
    data: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GalleryGroup(Base):
    """Группа фото в галерее на главной (например, «Спорткомплекс 1»)."""

    __tablename__ = "gallery_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)                      # заголовок группы
    subtitle: Mapped[str] = mapped_column(String, default="")       # подпись под заголовком
    photos: Mapped[str] = mapped_column(String, default="")         # JSON-список путей к фото
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
