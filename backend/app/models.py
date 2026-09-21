from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, default="")
    capacity: Mapped[int] = mapped_column(Integer, default=0)
    area_m2: Mapped[int] = mapped_column(Integer, default=0)
    image: Mapped[str] = mapped_column(String, default="")
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
