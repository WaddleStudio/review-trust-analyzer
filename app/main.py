from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import create_db_and_tables
from app.api import endpoints

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Review Trust Analyzer", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(endpoints.router)

@app.get("/")
async def read_root():
    return FileResponse('app/static/index.html')
