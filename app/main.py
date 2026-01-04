from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import STORAGE_DIR
from app.database import init_db
from app.routes import router

app = FastAPI(title="QR SaaS", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


app.mount("/static", StaticFiles(directory=STORAGE_DIR), name="static")

