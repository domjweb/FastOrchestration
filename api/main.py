from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from typing import List, Optional, Any
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient as KVSecretClient
    HAVE_KEYVAULT = True
except Exception:
    DefaultAzureCredential = None
    KVSecretClient = None
    HAVE_KEYVAULT = False
from temporalio.client import Client
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
        "https://happy-smoke-0e8381a0f.1.azurestaticapps.net",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Initialize Temporal client and store it on app.state
    temporal_address = os.getenv('TEMPORAL_ADDRESS', 'temporal-frontend:7233')
    temporal_namespace = os.getenv('TEMPORAL_NAMESPACE', 'temporal-system')
    try:
        app.state.temporal_client = await Client.connect(temporal_address, namespace=temporal_namespace)
        print('Temporal client connected to', temporal_address)
    except Exception as e:
        app.state.temporal_client = None
        print('Warning: could not connect Temporal client:', e)
    # Initialize Cosmos async client/container if configured
    cosmos_conn = os.getenv('COSMOS_CONN')
    cosmos_db = os.getenv('COSMOS_DB')
    cosmos_container = os.getenv('COSMOS_CONTAINER')
    if cosmos_conn and cosmos_db and cosmos_container:
        try:
            client = AsyncCosmosClient.from_connection_string(cosmos_conn)
            # Do not create DB/container here — assume they exist in production; get client handles
            db_client = client.get_database_client(cosmos_db)
            container_client = db_client.get_container_client(cosmos_container)
            app.state.cosmos_client = client
            app.state.cosmos_container = container_client
            print('Cosmos client initialized for', cosmos_db, cosmos_container)
        except Exception as e:
            app.state.cosmos_client = None
            app.state.cosmos_container = None
            print('Warning: could not initialize Cosmos client:', e)
    # If Key Vault is configured and cosmos env not set, try to fetch the connection string
    keyvault_url = os.getenv('KEYVAULT_URL')
    keyvault_cosmos_secret = os.getenv('KEYVAULT_COSMOS_SECRET', 'COSMOS_CONN')
    if not cosmos_conn and keyvault_url and HAVE_KEYVAULT:
        try:
            cred = DefaultAzureCredential()
            kv = KVSecretClient(vault_url=keyvault_url, credential=cred)
            s = kv.get_secret(keyvault_cosmos_secret)
            app.state.cosmos_conn = s.value
            print('Fetched COSMOS_CONN from Key Vault')
        except Exception as e:
            print('Key Vault fetch failed:', e)

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
    # Start a RequestWorkflow in Temporal to drive request lifecycle
    try:
        client = getattr(app.state, 'temporal_client', None)
        if client is not None:
            # Start workflow with request id as input; let workflow default SLA be used
            # Use the Python client API to start a workflow: pass the workflow function name
            await client.start_workflow("RequestWorkflow", req.id, id=f"request-{req.id}", task_queue="requests-hub")
            print(f"Started workflow request-{req.id}")
        else:
            print('Temporal client not available; skipping workflow start')
    except Exception as e:
        print('Error starting Temporal workflow:', e)
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
async def get_request_events(
    id: int,
    limit: int = Query(50, ge=1, le=500),
    continuation_token: Optional[str] = Query(None, alias="continuationToken"),
    order: str = Query("asc", regex="^(asc|desc)$"),
):
    """Return audit events for a request stored in Cosmos DB.

    Paging is supported via Cosmos continuation tokens. `order` can be 'asc' or 'desc' and
    defaults to ascending by timestamp.
    """
    container = getattr(app.state, 'cosmos_container', None)
    if container is None:
        raise HTTPException(status_code=500, detail="Cosmos DB not configured")

    order_sql = "ASC" if order == "asc" else "DESC"
    query = "SELECT * FROM c WHERE c.requestId = @requestId ORDER BY c.ts {}".format(order_sql)
    parameters = [{"name": "@requestId", "value": id}]

    try:
        pages = container.query_items(
            query=query,
            parameters=parameters,
            partition_key=str(id),
        ).by_page(continuation_token=continuation_token, max_item_count=limit)

        items: List[Any] = []
        next_token: Optional[str] = None
        async for page in pages:
            # 'page' is a normal iterable of items for this page
            for it in page:
                items.append(it)
            # capture continuation token from the pages iterator
            try:
                next_token = pages.continuation_token
            except Exception:
                next_token = None
            break

        return {"events": items, "continuationToken": next_token, "count": len(items)}
    except CosmosHttpResponseError as e:
        print('Cosmos query error:', e)
        raise HTTPException(status_code=500, detail="Error querying audit events")
    except Exception as e:
        print('Unexpected error querying Cosmos:', e)
        raise HTTPException(status_code=500, detail="Internal error")
