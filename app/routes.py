import os
from typing import Optional
from pathlib import Path
from uuid import uuid4

import qrcode
import requests
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, PlainTextResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from user_agents import parse as parse_ua

from app import schemas
from app.auth import authenticate_user, create_access_token, get_current_user, hash_password
from app.config import STORAGE_DIR, PUBLIC_BASE_URL
from app.database import get_session
from app.models import QRCode, ScanEvent, User

router = APIRouter()

ERROR_MAP = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}


def _build_file_url(filename: str) -> str:
    return f"/static/{filename}"


def _geolocate(ip: str) -> tuple[Optional[str], Optional[str]]:
    url = os.getenv("GEOIP_URL")
    if not url or not ip:
        return None, None
    try:
        resp = requests.get(url.format(ip=ip), timeout=1.0)
        if resp.status_code != 200:
            return None, None
        data = resp.json()
        country = data.get("country_name") or data.get("country")
        city = data.get("city")
        return country, city
    except Exception:
        return None, None


def _save_qr_image(data: str, payload: schemas.QRCreate) -> str:
    """Gera a imagem e retorna o caminho absoluto salvo."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.png"
    filepath = STORAGE_DIR / filename

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_MAP[payload.erro],
        box_size=payload.box_size,
        border=payload.border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    imagem = qr.make_image(fill_color=payload.fill_color, back_color=payload.back_color)
    imagem.save(filepath)
    return str(filepath)


@router.post("/auth/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register_user(
    body: schemas.UserCreate, session: Session = Depends(get_session)
):  # pragma: no cover - endpoint
    """Cria uma conta gratuita (quantos usuários quiser)."""
    existing = select(User).where(User.email == body.email)
    if session.exec(existing).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

    user = User(email=body.email, password_hash=hash_password(body.password))
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token({"sub": user.email})
    return schemas.Token(access_token=token)


@router.post("/auth/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)
):  # pragma: no cover - endpoint
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Credenciais inválidas.")

    token = create_access_token({"sub": user.email})
    return schemas.Token(access_token=token)


@router.get("/me")
def current_user(me: User = Depends(get_current_user)):  # pragma: no cover - endpoint
    return {"id": me.id, "email": me.email, "created_at": me.created_at}


@router.post("/qrcodes", response_model=schemas.QRPublic, status_code=status.HTTP_201_CREATED)
def create_qr(
    payload: schemas.QRCreate,
    session: Session = Depends(get_session),
    me: User = Depends(get_current_user),
):  # pragma: no cover - endpoint
    # Primeiro cria o registro para obter o ID
    record = QRCode(
        user_id=me.id,
        text=payload.texto,
        trackable=payload.trackable,
        active=payload.active,
        file_path="",
        file_url="",
        error_correction=payload.erro,
        box_size=payload.box_size,
        border=payload.border,
        fill_color=payload.fill_color,
        back_color=payload.back_color,
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    data = payload.texto
    track_url = None
    if payload.trackable:
        track_url = f"{PUBLIC_BASE_URL}/track/{record.id}"
        data = track_url

    file_path = _save_qr_image(data, payload)
    file_name = Path(file_path).name
    file_url = _build_file_url(file_name)

    record.file_path = file_path
    record.file_url = file_url
    record.track_url = track_url
    record.trackable = payload.trackable
    session.add(record)
    session.commit()
    session.refresh(record)

    return schemas.QRPublic(
        id=record.id,
        texto=record.text,
        file_url=file_url,
        track_url=track_url,
        trackable=record.trackable,
        active=record.active,
        error_correction=record.error_correction,
        box_size=record.box_size,
        border=record.border,
        fill_color=record.fill_color,
        back_color=record.back_color,
        created_at=record.created_at,
        scans_count=record.scans_count,
    )


@router.patch("/qrcodes/{qr_id}", response_model=schemas.QRPublic)
def update_qr(
    qr_id: int,
    body: schemas.QRUpdate,
    session: Session = Depends(get_session),
    me: User = Depends(get_current_user),
):  # pragma: no cover - endpoint
    record = session.get(QRCode, qr_id)
    if not record or record.user_id != me.id:
        raise HTTPException(status_code=404, detail="QR Code não encontrado")

    if body.texto is not None:
        record.text = body.texto
    if body.trackable is not None:
        record.trackable = body.trackable
        record.track_url = f"{PUBLIC_BASE_URL}/track/{record.id}" if record.trackable else None
    if body.active is not None:
        record.active = body.active

    session.add(record)
    session.commit()
    session.refresh(record)

    return schemas.QRPublic(
        id=record.id,
        texto=record.text,
        file_url=record.file_url,
        track_url=record.track_url,
        trackable=record.trackable,
        active=record.active,
        error_correction=record.error_correction,
        box_size=record.box_size,
        border=record.border,
        fill_color=record.fill_color,
        back_color=record.back_color,
        created_at=record.created_at,
        scans_count=record.scans_count,
    )


@router.get("/qrcodes", response_model=list[schemas.QRPublic])
def list_qr(
    session: Session = Depends(get_session), me: User = Depends(get_current_user)
):  # pragma: no cover - endpoint
    statement = (
        select(QRCode)
        .where(QRCode.user_id == me.id)
        .order_by(QRCode.created_at.desc())
    )
    qrs = session.exec(statement).all()
    return [
        schemas.QRPublic(
            id=item.id,
            texto=item.text,
            file_url=item.file_url,
            track_url=item.track_url,
            trackable=item.trackable,
            active=item.active,
            error_correction=item.error_correction,
            box_size=item.box_size,
            border=item.border,
            fill_color=item.fill_color,
            back_color=item.back_color,
            created_at=item.created_at,
            scans_count=item.scans_count,
        )
        for item in qrs
    ]


@router.get("/analytics")
def analytics(
    session: Session = Depends(get_session), me: User = Depends(get_current_user)
):  # pragma: no cover - endpoint
    # Dados baseados em criação e eventos
    statement = select(QRCode).where(QRCode.user_id == me.id)
    all_qrs = session.exec(statement).all()

    total = len(all_qrs)
    last_created = max((qr.created_at for qr in all_qrs), default=None)
    scans_total = sum(qr.scans_count for qr in all_qrs)

    # Contagem de hoje
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    today = now.date()
    created_today = sum(1 for qr in all_qrs if qr.created_at.date() == today)

    scans_today = session.exec(
        select(ScanEvent).where(
            ScanEvent.scanned_at >= datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
        )
    ).all()

    top_qrs = sorted(all_qrs, key=lambda x: x.scans_count, reverse=True)[:5]

    recent_scans = session.exec(
        select(ScanEvent).order_by(ScanEvent.scanned_at.desc()).limit(20)
    ).all()

    return schemas.AnalyticsResponse(
        total_qrcodes=total,
        created_today=created_today,
        last_created_at=last_created,
        scans_total=scans_total,
        scans_today=len(scans_today),
        top_qrcodes=[
            schemas.QRPublic(
                id=item.id,
                texto=item.text,
                file_url=item.file_url,
                track_url=item.track_url,
                trackable=item.trackable,
                active=item.active,
                error_correction=item.error_correction,
                box_size=item.box_size,
                border=item.border,
                fill_color=item.fill_color,
                back_color=item.back_color,
                created_at=item.created_at,
                scans_count=item.scans_count,
            )
            for item in top_qrs
        ],
        recent_scans=[
            schemas.ScanEventPublic(
                id=scan.id,
                qr_id=scan.qr_id,
                scanned_at=scan.scanned_at,
                ip=scan.ip,
                device_type=scan.device_type,
                os=scan.os,
                browser=scan.browser,
                country=scan.country,
                city=scan.city,
                referer=scan.referer,
            )
            for scan in recent_scans
        ],
    )


@router.get("/track/{qr_id}")
def track_qr(qr_id: int, request: Request, session: Session = Depends(get_session)):
    record = session.get(QRCode, qr_id)
    if not record:
        raise HTTPException(status_code=404, detail="QR Code não encontrado")

    if not record.active:
        raise HTTPException(status_code=410, detail="QR Code inativo")

    if record.trackable:
        record.scans_count += 1
        # Captura ip/ua
        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
            request.client.host if request.client else None
        )
        ua_str = request.headers.get("user-agent", "")
        ua = parse_ua(ua_str) if ua_str else None
        device_type = "mobile" if ua and ua.is_mobile else "tablet" if ua and ua.is_tablet else "desktop"
        os_name = f"{ua.os.family} {ua.os.version_string}" if ua else None
        browser_name = f"{ua.browser.family} {ua.browser.version_string}" if ua else None
        country, city = _geolocate(ip) if ip else (None, None)

        scan_event = ScanEvent(
            qr_id=record.id,
            ip=ip,
            user_agent=ua_str or None,
            device_type=device_type,
            os=os_name,
            browser=browser_name,
            country=country,
            city=city,
            referer=request.headers.get("referer"),
        )
        session.add(scan_event)
        session.add(record)
        session.commit()

    if record.text.lower().startswith("http"):
        return RedirectResponse(url=record.text)

    return PlainTextResponse(record.text)


@router.get("/qrcodes/{qr_id}/scans/export")
def export_scans_csv(qr_id: int, session: Session = Depends(get_session), me: User = Depends(get_current_user)):
    record = session.get(QRCode, qr_id)
    if not record or record.user_id != me.id:
        raise HTTPException(status_code=404, detail="QR Code não encontrado")

    scans = session.exec(select(ScanEvent).where(ScanEvent.qr_id == qr_id).order_by(ScanEvent.scanned_at.desc())).all()

    def iter_csv():
        yield "id,scanned_at,ip,device,os,browser,country,city,referer\n"
        for s in scans:
            row = [
                s.id,
                s.scanned_at.isoformat(),
                s.ip or "",
                s.device_type or "",
                s.os or "",
                s.browser or "",
                s.country or "",
                s.city or "",
                s.referer or "",
            ]
            yield ",".join(str(v).replace(",", " ") for v in row) + "\n"

    return StreamingResponse(iter_csv(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="qr_{qr_id}_scans.csv"'})

