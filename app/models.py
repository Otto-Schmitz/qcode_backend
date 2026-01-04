from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, sa_column_kwargs={"unique": True})
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    qrcodes: list["QRCode"] = Relationship(back_populates="owner")


class QRCode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    text: str
    track_url: Optional[str] = None
    trackable: bool = Field(default=True)
    active: bool = Field(default=True)
    file_path: str
    file_url: str
    error_correction: str
    box_size: int
    border: int
    fill_color: str
    back_color: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scans_count: int = Field(default=0)

    owner: Optional[User] = Relationship(back_populates="qrcodes")


class ScanEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    qr_id: int = Field(foreign_key="qrcode.id", index=True)
    scanned_at: datetime = Field(default_factory=datetime.utcnow)
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None
    os: Optional[str] = None
    browser: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    referer: Optional[str] = None

