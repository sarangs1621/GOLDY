from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
from decimal import Decimal
from bson import Decimal128

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

def decimal_to_float(obj):
    if isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    elif isinstance(obj, Decimal128):
        return float(obj.to_decimal())
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def float_to_decimal128(value):
    if value is None:
        return None
    return Decimal128(Decimal(str(value)))

class UserRole(BaseModel):
    role: str
    permissions: List[str] = []

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "staff"

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class InventoryHeader(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    is_deleted: bool = False

class StockMovement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    movement_type: str
    header_id: str
    header_name: str
    description: str
    qty_delta: float
    weight_delta: float
    purity: int
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    created_by: str
    notes: Optional[str] = None
    is_deleted: bool = False

class Party(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    party_type: str
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    is_deleted: bool = False

class JobCardItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    description: str
    qty: int
    weight_in: float
    weight_out: Optional[float] = None
    purity: int
    work_type: str
    remarks: Optional[str] = None

class JobCard(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_card_number: str
    card_type: str
    date_created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivery_date: Optional[datetime] = None
    status: str = "created"
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None
    items: List[JobCardItem] = []
    notes: Optional[str] = None
    created_by: str
    is_deleted: bool = False

class InvoiceItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    qty: int
    weight: float
    purity: int
    metal_rate: float
    gold_value: float
    making_value: float
    vat_percent: float
    vat_amount: float
    line_total: float

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    invoice_type: str = "sale"
    payment_status: str = "unpaid"
    items: List[InvoiceItem] = []
    subtotal: float = 0
    vat_total: float = 0
    grand_total: float = 0
    paid_amount: float = 0
    balance_due: float = 0
    notes: Optional[str] = None
    jobcard_id: Optional[str] = None
    created_by: str
    is_deleted: bool = False

class Account(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    account_type: str
    opening_balance: float = 0
    current_balance: float = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    is_deleted: bool = False

class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_number: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    transaction_type: str
    mode: str
    account_id: str
    account_name: str
    party_id: Optional[str] = None
    party_name: Optional[str] = None
    amount: float
    category: str
    notes: Optional[str] = None
    created_by: str
    is_deleted: bool = False

class DailyClosing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime
    opening_cash: float
    total_credit: float
    total_debit: float
    expected_closing: float
    actual_closing: float
    difference: float
    is_locked: bool = False
    closed_by: str
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str
    user_name: str
    module: str
    record_id: str
    action: str
    changes: Optional[Dict[str, Any]] = None

async def create_audit_log(user_id: str, user_name: str, module: str, record_id: str, action: str, changes: Optional[Dict] = None):
    log = AuditLog(
        user_id=user_id,
        user_name=user_name,
        module=module,
        record_id=record_id,
        action=action,
        changes=changes
    )
    await db.audit_logs.insert_one(log.model_dump())

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        
        user_doc = await db.users.find_one({"id": user_id, "is_deleted": False}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        
        return User(**user_doc)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"username": user_data.username, "is_deleted": False})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = pwd_context.hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    user_dict = user.model_dump()
    user_dict['hashed_password'] = hashed_password
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    return user

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"username": credentials.username, "is_deleted": False}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not pwd_context.verify(credentials.password, user_doc.get('hashed_password', '')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user_doc.get('is_active', False):
        raise HTTPException(status_code=403, detail="User is inactive")
    
    user = User(**user_doc)
    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    
    return TokenResponse(access_token=token, user=user)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_user)):
    users = await db.users.find({"is_deleted": False}, {"_id": 0, "hashed_password": 0}).to_list(1000)
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    return users

@api_router.get("/inventory/headers", response_model=List[InventoryHeader])
async def get_inventory_headers(current_user: User = Depends(get_current_user)):
    headers = await db.inventory_headers.find({"is_deleted": False}, {"_id": 0}).to_list(1000)
    return headers

@api_router.post("/inventory/headers", response_model=InventoryHeader)
async def create_inventory_header(header_data: dict, current_user: User = Depends(get_current_user)):
    header = InventoryHeader(name=header_data['name'], created_by=current_user.id)
    await db.inventory_headers.insert_one(header.model_dump())
    await create_audit_log(current_user.id, current_user.full_name, "inventory_header", header.id, "create")
    return header

@api_router.get("/inventory/movements", response_model=List[StockMovement])
async def get_stock_movements(header_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"is_deleted": False}
    if header_id:
        query['header_id'] = header_id
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    return movements

@api_router.post("/inventory/movements", response_model=StockMovement)
async def create_stock_movement(movement_data: dict, current_user: User = Depends(get_current_user)):
    header = await db.inventory_headers.find_one({"id": movement_data['header_id']}, {"_id": 0})
    if not header:
        raise HTTPException(status_code=404, detail="Header not found")
    
    movement = StockMovement(
        movement_type=movement_data['movement_type'],
        header_id=movement_data['header_id'],
        header_name=header['name'],
        description=movement_data['description'],
        qty_delta=movement_data['qty_delta'],
        weight_delta=movement_data['weight_delta'],
        purity=movement_data['purity'],
        notes=movement_data.get('notes'),
        created_by=current_user.id
    )
    
    await db.stock_movements.insert_one(movement.model_dump())
    await create_audit_log(current_user.id, current_user.full_name, "stock_movement", movement.id, "create")
    return movement

@api_router.get("/inventory/stock-totals")
async def get_stock_totals(current_user: User = Depends(get_current_user)):
    pipeline = [
        {"$match": {"is_deleted": False}},
        {"$group": {
            "_id": "$header_id",
            "header_name": {"$first": "$header_name"},
            "total_qty": {"$sum": "$qty_delta"},
            "total_weight": {"$sum": "$weight_delta"}
        }}
    ]
    totals = await db.stock_movements.aggregate(pipeline).to_list(1000)
    return [{"header_id": t['_id'], "header_name": t['header_name'], "total_qty": t['total_qty'], "total_weight": t['total_weight']} for t in totals]

@api_router.get("/parties", response_model=List[Party])
async def get_parties(party_type: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"is_deleted": False}
    if party_type:
        query['party_type'] = party_type
    parties = await db.parties.find(query, {"_id": 0}).to_list(1000)
    return parties

@api_router.post("/parties", response_model=Party)
async def create_party(party_data: dict, current_user: User = Depends(get_current_user)):
    party = Party(**party_data, created_by=current_user.id)
    await db.parties.insert_one(party.model_dump())
    await create_audit_log(current_user.id, current_user.full_name, "party", party.id, "create")
    return party

@api_router.get("/parties/{party_id}/ledger")
async def get_party_ledger(party_id: str, current_user: User = Depends(get_current_user)):
    invoices = await db.invoices.find({"customer_id": party_id, "is_deleted": False}, {"_id": 0}).to_list(1000)
    transactions = await db.transactions.find({"party_id": party_id, "is_deleted": False}, {"_id": 0}).to_list(1000)
    
    outstanding = 0
    for inv in invoices:
        outstanding += inv.get('balance_due', 0)
    
    return {"invoices": invoices, "transactions": transactions, "outstanding": outstanding}

@api_router.get("/parties/outstanding-summary")
async def get_outstanding_summary(current_user: User = Depends(get_current_user)):
    invoices = await db.invoices.find({"is_deleted": False, "payment_status": {"$ne": "paid"}}, {"_id": 0}).to_list(10000)
    
    total_customer_due = sum(inv.get('balance_due', 0) for inv in invoices)
    
    party_outstanding = {}
    for inv in invoices:
        cid = inv.get('customer_id')
        if cid:
            if cid not in party_outstanding:
                party_outstanding[cid] = {"customer_id": cid, "customer_name": inv.get('customer_name', ''), "outstanding": 0}
            party_outstanding[cid]['outstanding'] += inv.get('balance_due', 0)
    
    top_10 = sorted(party_outstanding.values(), key=lambda x: x['outstanding'], reverse=True)[:10]
    
    return {"total_customer_due": total_customer_due, "top_10_outstanding": top_10}

@api_router.get("/jobcards", response_model=List[JobCard])
async def get_jobcards(current_user: User = Depends(get_current_user)):
    jobcards = await db.jobcards.find({"is_deleted": False}, {"_id": 0}).sort("date_created", -1).to_list(1000)
    return jobcards

@api_router.post("/jobcards", response_model=JobCard)
async def create_jobcard(jobcard_data: dict, current_user: User = Depends(get_current_user)):
    year = datetime.now(timezone.utc).year
    count = await db.jobcards.count_documents({"job_card_number": {"$regex": f"^JC-{year}"}})
    job_card_number = f"JC-{year}-{str(count + 1).zfill(4)}"
    
    jobcard = JobCard(**jobcard_data, job_card_number=job_card_number, created_by=current_user.id)
    await db.jobcards.insert_one(jobcard.model_dump())
    await create_audit_log(current_user.id, current_user.full_name, "jobcard", jobcard.id, "create")
    return jobcard

@api_router.patch("/jobcards/{jobcard_id}")
async def update_jobcard(jobcard_id: str, update_data: dict, current_user: User = Depends(get_current_user)):
    await db.jobcards.update_one({"id": jobcard_id}, {"$set": update_data})
    await create_audit_log(current_user.id, current_user.full_name, "jobcard", jobcard_id, "update", update_data)
    return {"message": "Updated successfully"}

@api_router.post("/jobcards/{jobcard_id}/convert-to-invoice")
async def convert_jobcard_to_invoice(jobcard_id: str, current_user: User = Depends(get_current_user)):
    jobcard = await db.jobcards.find_one({"id": jobcard_id, "is_deleted": False}, {"_id": 0})
    if not jobcard:
        raise HTTPException(status_code=404, detail="Job card not found")
    
    year = datetime.now(timezone.utc).year
    count = await db.invoices.count_documents({"invoice_number": {"$regex": f"^INV-{year}"}})
    invoice_number = f"INV-{year}-{str(count + 1).zfill(4)}"
    
    vat_percent = 5.0
    invoice_items = []
    subtotal = 0
    vat_total = 0
    
    for item in jobcard.get('items', []):
        metal_rate = 20.0
        weight = item.get('weight_out', item.get('weight_in', 0))
        gold_value = weight * metal_rate
        making_value = 5.0
        vat_amount = (gold_value + making_value) * vat_percent / 100
        line_total = gold_value + making_value + vat_amount
        
        invoice_items.append(InvoiceItem(
            description=item.get('description', ''),
            qty=item.get('qty', 1),
            weight=weight,
            purity=item.get('purity', 916),
            metal_rate=metal_rate,
            gold_value=gold_value,
            making_value=making_value,
            vat_percent=vat_percent,
            vat_amount=vat_amount,
            line_total=line_total
        ))
        
        subtotal += gold_value + making_value
        vat_total += vat_amount
    
    grand_total = subtotal + vat_total
    
    invoice = Invoice(
        invoice_number=invoice_number,
        customer_id=jobcard.get('customer_id'),
        customer_name=jobcard.get('customer_name'),
        invoice_type="service",
        items=invoice_items,
        subtotal=subtotal,
        vat_total=vat_total,
        grand_total=grand_total,
        balance_due=grand_total,
        jobcard_id=jobcard_id,
        created_by=current_user.id
    )
    
    await db.invoices.insert_one(invoice.model_dump())
    await create_audit_log(current_user.id, current_user.full_name, "invoice", invoice.id, "create_from_jobcard")
    return invoice

@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices(current_user: User = Depends(get_current_user)):
    invoices = await db.invoices.find({"is_deleted": False}, {"_id": 0}).sort("date", -1).to_list(1000)
    return invoices

@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_data: dict, current_user: User = Depends(get_current_user)):
    year = datetime.now(timezone.utc).year
    count = await db.invoices.count_documents({"invoice_number": {"$regex": f"^INV-{year}"}})
    invoice_number = f"INV-{year}-{str(count + 1).zfill(4)}"
    
    invoice = Invoice(**invoice_data, invoice_number=invoice_number, created_by=current_user.id)
    await db.invoices.insert_one(invoice.model_dump())
    
    for item in invoice.items:
        if item.weight > 0:
            movement = StockMovement(
                movement_type="Stock OUT",
                header_id="",
                header_name=item.description,
                description=f"Invoice {invoice_number}",
                qty_delta=-item.qty,
                weight_delta=-item.weight,
                purity=item.purity,
                reference_type="invoice",
                reference_id=invoice.id,
                created_by=current_user.id
            )
            await db.stock_movements.insert_one(movement.model_dump())
    
    await create_audit_log(current_user.id, current_user.full_name, "invoice", invoice.id, "create")
    return invoice

@api_router.get("/accounts", response_model=List[Account])
async def get_accounts(current_user: User = Depends(get_current_user)):
    accounts = await db.accounts.find({"is_deleted": False}, {"_id": 0}).to_list(1000)
    return accounts

@api_router.post("/accounts", response_model=Account)
async def create_account(account_data: dict, current_user: User = Depends(get_current_user)):
    account = Account(**account_data, created_by=current_user.id)
    await db.accounts.insert_one(account.model_dump())
    await create_audit_log(current_user.id, current_user.full_name, "account", account.id, "create")
    return account

@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(current_user: User = Depends(get_current_user)):
    transactions = await db.transactions.find({"is_deleted": False}, {"_id": 0}).sort("date", -1).to_list(1000)
    return transactions

@api_router.post("/transactions", response_model=Transaction)
async def create_transaction(transaction_data: dict, current_user: User = Depends(get_current_user)):
    year = datetime.now(timezone.utc).year
    count = await db.transactions.count_documents({"transaction_number": {"$regex": f"^TXN-{year}"}})
    transaction_number = f"TXN-{year}-{str(count + 1).zfill(4)}"
    
    account = await db.accounts.find_one({"id": transaction_data['account_id']}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    transaction = Transaction(
        **transaction_data,
        transaction_number=transaction_number,
        account_name=account['name'],
        created_by=current_user.id
    )
    
    await db.transactions.insert_one(transaction.model_dump())
    
    delta = transaction.amount if transaction.transaction_type == "credit" else -transaction.amount
    await db.accounts.update_one(
        {"id": transaction.account_id},
        {"$inc": {"current_balance": delta}}
    )
    
    await create_audit_log(current_user.id, current_user.full_name, "transaction", transaction.id, "create")
    return transaction

@api_router.get("/daily-closings", response_model=List[DailyClosing])
async def get_daily_closings(current_user: User = Depends(get_current_user)):
    closings = await db.daily_closings.find({}, {"_id": 0}).sort("date", -1).to_list(1000)
    return closings

@api_router.post("/daily-closings", response_model=DailyClosing)
async def create_daily_closing(closing_data: dict, current_user: User = Depends(get_current_user)):
    closing = DailyClosing(**closing_data, closed_by=current_user.id)
    await db.daily_closings.insert_one(closing.model_dump())
    await create_audit_log(current_user.id, current_user.full_name, "daily_closing", closing.id, "create")
    return closing

@api_router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(module: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {}
    if module:
        query['module'] = module
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(500).to_list(500)
    return logs

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
