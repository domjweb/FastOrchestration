from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import enum
import os


# Use SSL context for Azure PostgreSQL (asyncpg)
import ssl
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/requests_hub")
ssl_context = ssl.create_default_context()
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    connect_args={"ssl": ssl_context}
)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class RequestStatus(str, enum.Enum):
    open = "open"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.open, nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)

class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    blob_url = Column(String(500), nullable=False)

# Pydantic models
class RequestCreate(BaseModel):
    title: str
    description: Optional[str]
    type: str
    priority: str
    attachments: Optional[List[str]] = []

class RequestUpdate(BaseModel):
    status: RequestStatus
    assignee_id: Optional[int]

class RequestOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    type: str
    priority: str
    status: RequestStatus
    assignee_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class AttachmentOut(BaseModel):
    id: int
    request_id: int
    blob_url: str
    class Config:
        from_attributes = True

# Dependency
async def get_db():
    async with SessionLocal() as session:
        yield session

app = FastAPI(title="Requests Hub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/api/requests", response_model=RequestOut)
async def create_request(data: RequestCreate, db: AsyncSession = Depends(get_db)):
    req = Request(
        title=data.title,
        description=data.description,
        type=data.type,
        priority=data.priority,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    # Attachments would be handled here (Azure Blob integration placeholder)
    return req

@app.get("/api/requests", response_model=List[RequestOut])
async def list_requests(status: Optional[RequestStatus] = None, page: int = 1, db: AsyncSession = Depends(get_db)):
    q = await db.execute(
        Request.__table__.select().where(Request.status == status) if status else Request.__table__.select()
    )
    results = q.mappings().all()
    return [RequestOut.model_validate(r) for r in results]

@app.patch("/api/requests/{id}", response_model=RequestOut)
async def update_request(id: int, data: RequestUpdate, db: AsyncSession = Depends(get_db)):
    q = await db.execute(Request.__table__.select().where(Request.id == id))
    req = q.fetchone()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    await db.execute(
        Request.__table__.update().where(Request.id == id).values(**data.model_dump())
    )
    await db.commit()
    q = await db.execute(Request.__table__.select().where(Request.id == id))
    updated = q.fetchone()
    return RequestOut.model_validate(dict(updated))

@app.post("/api/requests/{id}/attachments", response_model=AttachmentOut)
async def upload_attachment(id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # Placeholder: upload to Azure Blob, get URL
    blob_url = f"https://blob.example.com/{file.filename}"
    att = Attachment(request_id=id, blob_url=blob_url)
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return att

@app.get("/api/requests/{id}/events")
async def get_request_events(id: int):
    # Placeholder: fetch from Cosmos DB
    return [{"eventType": "created", "timestamp": "2025-10-14T12:00:00Z", "requestId": id}]
