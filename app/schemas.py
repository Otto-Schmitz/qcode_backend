from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QRCreate(BaseModel):
    texto: str = Field(..., description="Conteúdo a codificar")
    box_size: int = Field(10, ge=1, le=40)
    border: int = Field(4, ge=1, le=16)
    erro: str = Field("M", pattern="^[LMQH]$")
    fill_color: str = Field("black")
    back_color: str = Field("white")
    trackable: bool = Field(True, description="Se true, gera link de tracking")
    active: bool = Field(True, description="Se false, retorna inativo no tracking")


class QRPublic(BaseModel):
    id: int
    texto: str
    file_url: str
    track_url: Optional[str]
    trackable: bool
    active: bool
    error_correction: str
    box_size: int
    border: int
    fill_color: str
    back_color: str
    created_at: datetime
    scans_count: int = 0

    class Config:
        from_attributes = True


class QRUpdate(BaseModel):
    texto: Optional[str] = None
    trackable: Optional[bool] = None
    active: Optional[bool] = None


class ScanEventPublic(BaseModel):
    id: int
    qr_id: int
    scanned_at: datetime
    ip: Optional[str]
    device_type: Optional[str]
    os: Optional[str]
    browser: Optional[str]
    country: Optional[str]
    city: Optional[str]
    referer: Optional[str]

    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    total_qrcodes: int
    created_today: int
    last_created_at: Optional[datetime]
    scans_total: int
    scans_today: int
    top_qrcodes: list[QRPublic]
    recent_scans: list[ScanEventPublic]

