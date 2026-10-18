from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.database import engine
from app.routers import heroes, teams 

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

# Thêm tiêu đề và version cho OpenAPI Docs
app = FastAPI(
    title="Heroes API", 
    version="1.0.0", 
    lifespan=lifespan,
    openapi_tags=[
        {"name": "heroes", "description": "Create, read, update and delete heroes."},
        {"name": "teams", "description": "Teams and the heroes that belong to them."}
    ]
)

# Thêm CORSMiddleware 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(heroes.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
