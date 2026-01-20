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
    current_qty: float = 0.0  # Direct stock tracking
    current_weight: float = 0.0  # Direct weight tracking in grams
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
    making_charge_type: Optional[str] = None  # 'flat' or 'per_gram'
    making_charge_value: Optional[float] = None
    vat_percent: Optional[float] = None
    vat_amount: Optional[float] = None

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
    locked: bool = False  # True when linked invoice is finalized
    locked_at: Optional[datetime] = None
    locked_by: Optional[str] = None
    created_by: str
    is_deleted: bool = False

class InvoiceItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: Optional[str] = None  # Inventory category for stock tracking
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
    due_date: Optional[datetime] = None  # For overdue calculations, defaults to invoice date
    customer_type: str = "saved"  # "saved" or "walk_in"
    customer_id: Optional[str] = None  # For saved customers only
    customer_name: Optional[str] = None  # For saved customers only
    walk_in_name: Optional[str] = None  # For walk-in customers only
    walk_in_phone: Optional[str] = None  # For walk-in customers only
    invoice_type: str = "sale"
    payment_status: str = "unpaid"
    status: str = "draft"  # "draft" or "finalized" - controls when stock is deducted
    finalized_at: Optional[datetime] = None
    finalized_by: Optional[str] = None
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

@api_router.patch("/users/{user_id}")
async def update_user(user_id: str, update_data: dict, current_user: User = Depends(get_current_user)):
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Not authorized to update users")
    
    existing = await db.users.find_one({"id": user_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow password updates through this endpoint
    if 'password' in update_data:
        del update_data['password']
    if 'hashed_password' in update_data:
        del update_data['hashed_password']
    
    await db.users.update_one({"id": user_id}, {"$set": update_data})
    await create_audit_log(current_user.id, current_user.full_name, "user", user_id, "update", update_data)
    return {"message": "User updated successfully"}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can delete users")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    existing = await db.users.find_one({"id": user_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc), "deleted_by": current_user.id}}
    )
    await create_audit_log(current_user.id, current_user.full_name, "user", user_id, "delete")
    return {"message": "User deleted successfully"}

@api_router.post("/users/{user_id}/change-password")
async def change_password(user_id: str, password_data: dict, current_user: User = Depends(get_current_user)):
    # Users can change their own password, admins can change anyone's
    if user_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
    
    existing = await db.users.find_one({"id": user_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_password = password_data.get('new_password')
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    hashed_password = pwd_context.hash(new_password)
    await db.users.update_one({"id": user_id}, {"$set": {"hashed_password": hashed_password}})
    await create_audit_log(current_user.id, current_user.full_name, "user", user_id, "password_change")
    return {"message": "Password changed successfully"}

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
    
    # Insert stock movement for audit trail
    await db.stock_movements.insert_one(movement.model_dump())
    
    # DIRECT UPDATE: Update header's current quantity and weight
    new_qty = header.get('current_qty', 0) + movement_data['qty_delta']
    new_weight = header.get('current_weight', 0) + movement_data['weight_delta']
    
    # Validate stock doesn't go negative
    if new_qty < 0 or new_weight < 0:
        # Delete the movement we just created
        await db.stock_movements.delete_one({"id": movement.id})
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient stock. Available: {header.get('current_qty', 0)} qty, {header.get('current_weight', 0)}g. Requested: {abs(movement_data['qty_delta'])} qty, {abs(movement_data['weight_delta'])}g"
        )
    
    await db.inventory_headers.update_one(
        {"id": movement_data['header_id']},
        {"$set": {"current_qty": new_qty, "current_weight": new_weight}}
    )
    
    await create_audit_log(current_user.id, current_user.full_name, "stock_movement", movement.id, "create")
    return movement

@api_router.get("/inventory/stock-totals")
async def get_stock_totals(current_user: User = Depends(get_current_user)):
    # Return current stock directly from inventory headers
    headers = await db.inventory_headers.find({"is_deleted": False}, {"_id": 0}).to_list(1000)
    return [
        {
            "header_id": h['id'], 
            "header_name": h['name'], 
            "total_qty": h.get('current_qty', 0), 
            "total_weight": h.get('current_weight', 0)
        } 
        for h in headers
    ]

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

@api_router.get("/parties/{party_id}", response_model=Party)
async def get_party(party_id: str, current_user: User = Depends(get_current_user)):
    party = await db.parties.find_one({"id": party_id, "is_deleted": False}, {"_id": 0})
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    return Party(**party)

@api_router.patch("/parties/{party_id}", response_model=Party)
async def update_party(party_id: str, party_data: dict, current_user: User = Depends(get_current_user)):
    existing = await db.parties.find_one({"id": party_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="Party not found")
    
    await db.parties.update_one({"id": party_id}, {"$set": party_data})
    await create_audit_log(current_user.id, current_user.full_name, "party", party_id, "update", party_data)
    
    updated = await db.parties.find_one({"id": party_id}, {"_id": 0})
    return Party(**updated)

@api_router.delete("/parties/{party_id}")
async def delete_party(party_id: str, current_user: User = Depends(get_current_user)):
    existing = await db.parties.find_one({"id": party_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="Party not found")
    
    await db.parties.update_one(
        {"id": party_id},
        {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc), "deleted_by": current_user.id}}
    )
    await create_audit_log(current_user.id, current_user.full_name, "party", party_id, "delete")
    return {"message": "Party deleted successfully"}

@api_router.get("/parties/{party_id}/ledger")
async def get_party_ledger(party_id: str, current_user: User = Depends(get_current_user)):
    invoices = await db.invoices.find({"customer_id": party_id, "is_deleted": False}, {"_id": 0}).to_list(1000)
    transactions = await db.transactions.find({"party_id": party_id, "is_deleted": False}, {"_id": 0}).to_list(1000)
    
    outstanding = 0
    for inv in invoices:
        outstanding += inv.get('balance_due', 0)
    
    return {"invoices": invoices, "transactions": transactions, "outstanding": outstanding}

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

@api_router.get("/jobcards/{jobcard_id}", response_model=JobCard)
async def get_jobcard(jobcard_id: str, current_user: User = Depends(get_current_user)):
    jobcard = await db.jobcards.find_one({"id": jobcard_id, "is_deleted": False}, {"_id": 0})
    if not jobcard:
        raise HTTPException(status_code=404, detail="Job card not found")
    return JobCard(**jobcard)

@api_router.patch("/jobcards/{jobcard_id}")
async def update_jobcard(jobcard_id: str, update_data: dict, current_user: User = Depends(get_current_user)):
    existing = await db.jobcards.find_one({"id": jobcard_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="Job card not found")
    
    # Check if job card is locked (linked to finalized invoice)
    if existing.get("locked", False):
        # Admin override: Allow admins to edit locked job cards
        if current_user.role == 'admin':
            # Perform the update
            await db.jobcards.update_one({"id": jobcard_id}, {"$set": update_data})
            
            # Log admin override with special action
            override_details = {
                "action": "admin_override_edit_locked_jobcard",
                "reason": "Admin edited a locked job card that is linked to a finalized invoice",
                "locked_at": existing.get("locked_at"),
                "locked_by": existing.get("locked_by"),
                "changes": update_data
            }
            await create_audit_log(
                current_user.id, 
                current_user.full_name, 
                "jobcard", 
                jobcard_id, 
                "admin_override_edit", 
                override_details
            )
            
            return {
                "message": "Job card updated successfully (admin override)",
                "warning": "This job card is locked and linked to a finalized invoice"
            }
        else:
            # Non-admin users cannot edit locked job cards
            raise HTTPException(
                status_code=403, 
                detail="Cannot edit locked job card. This job card is linked to a finalized invoice. Only admins can override."
            )
    
    # Normal update for unlocked job cards
    await db.jobcards.update_one({"id": jobcard_id}, {"$set": update_data})
    await create_audit_log(current_user.id, current_user.full_name, "jobcard", jobcard_id, "update", update_data)
    return {"message": "Updated successfully"}

@api_router.delete("/jobcards/{jobcard_id}")
async def delete_jobcard(jobcard_id: str, current_user: User = Depends(get_current_user)):
    existing = await db.jobcards.find_one({"id": jobcard_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="Job card not found")
    
    # Check if job card is locked (linked to finalized invoice)
    if existing.get("locked", False):
        # Admin override: Allow admins to delete locked job cards
        if current_user.role == 'admin':
            # Perform the delete (soft delete)
            await db.jobcards.update_one(
                {"id": jobcard_id},
                {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc), "deleted_by": current_user.id}}
            )
            
            # Log admin override with special action
            override_details = {
                "action": "admin_override_delete_locked_jobcard",
                "reason": "Admin deleted a locked job card that is linked to a finalized invoice",
                "locked_at": existing.get("locked_at"),
                "locked_by": existing.get("locked_by"),
                "jobcard_number": existing.get("job_card_number"),
                "customer_name": existing.get("customer_name")
            }
            await create_audit_log(
                current_user.id, 
                current_user.full_name, 
                "jobcard", 
                jobcard_id, 
                "admin_override_delete", 
                override_details
            )
            
            return {
                "message": "Job card deleted successfully (admin override)",
                "warning": "This job card was locked and linked to a finalized invoice"
            }
        else:
            # Non-admin users cannot delete locked job cards
            raise HTTPException(
                status_code=403, 
                detail="Cannot delete locked job card. This job card is linked to a finalized invoice. Only admins can override."
            )
    
    # Normal delete for unlocked job cards
    await db.jobcards.update_one(
        {"id": jobcard_id},
        {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc), "deleted_by": current_user.id}}
    )
    await create_audit_log(current_user.id, current_user.full_name, "jobcard", jobcard_id, "delete")
    return {"message": "Job card deleted successfully"}

@api_router.post("/jobcards/{jobcard_id}/convert-to-invoice")
async def convert_jobcard_to_invoice(jobcard_id: str, invoice_data: dict, current_user: User = Depends(get_current_user)):
    jobcard = await db.jobcards.find_one({"id": jobcard_id, "is_deleted": False}, {"_id": 0})
    if not jobcard:
        raise HTTPException(status_code=404, detail="Job card not found")
    
    # Extract customer type and details from invoice_data
    customer_type = invoice_data.get('customer_type', 'saved')
    
    # Validate customer data based on type
    if customer_type == 'saved':
        if not invoice_data.get('customer_id'):
            raise HTTPException(status_code=400, detail="customer_id is required for saved customers")
    elif customer_type == 'walk_in':
        if not invoice_data.get('walk_in_name'):
            raise HTTPException(status_code=400, detail="walk_in_name is required for walk-in customers")
    
    year = datetime.now(timezone.utc).year
    count = await db.invoices.count_documents({"invoice_number": {"$regex": f"^INV-{year}"}})
    invoice_number = f"INV-{year}-{str(count + 1).zfill(4)}"
    
    vat_percent = 5.0
    invoice_items = []
    subtotal = 0
    vat_total = 0
    
    for item in jobcard.get('items', []):
        metal_rate = 20.0
        weight = item.get('weight_out') or item.get('weight_in') or 0
        weight = float(weight) if weight else 0.0
        gold_value = weight * metal_rate
        
        # Use making charge from job card if provided, otherwise use default
        if item.get('making_charge_value') is not None:
            if item.get('making_charge_type') == 'per_gram':
                making_value = float(item.get('making_charge_value', 0)) * weight
            else:  # flat
                making_value = float(item.get('making_charge_value', 0))
        else:
            making_value = 5.0  # Default
        
        # Use VAT from job card if provided, otherwise use default
        item_vat_percent = item.get('vat_percent') or vat_percent
        vat_amount = (gold_value + making_value) * item_vat_percent / 100
        line_total = gold_value + making_value + vat_amount
        
        invoice_items.append(InvoiceItem(
            category=item.get('category', ''),  # Store category for stock tracking
            description=item.get('description', ''),
            qty=item.get('qty', 1),
            weight=weight,
            purity=item.get('purity', 916),
            metal_rate=metal_rate,
            gold_value=gold_value,
            making_value=making_value,
            vat_percent=item_vat_percent,
            vat_amount=vat_amount,
            line_total=line_total
        ))
        
        subtotal += gold_value + making_value
        vat_total += vat_amount
    
    grand_total = subtotal + vat_total
    
    # Create invoice with customer type specific fields
    invoice_dict = {
        "invoice_number": invoice_number,
        "customer_type": customer_type,
        "invoice_type": "service",
        "items": [item.model_dump() for item in invoice_items],
        "subtotal": subtotal,
        "vat_total": vat_total,
        "grand_total": grand_total,
        "balance_due": grand_total,
        "jobcard_id": jobcard_id,
        "created_by": current_user.id
    }
    
    # Add customer-specific fields
    if customer_type == 'saved':
        invoice_dict["customer_id"] = invoice_data.get('customer_id')
        invoice_dict["customer_name"] = invoice_data.get('customer_name')
    else:  # walk_in
        invoice_dict["walk_in_name"] = invoice_data.get('walk_in_name')
        invoice_dict["walk_in_phone"] = invoice_data.get('walk_in_phone', '')
    
    invoice = Invoice(**invoice_dict)
    
    await db.invoices.insert_one(invoice.model_dump())
    await create_audit_log(current_user.id, current_user.full_name, "invoice", invoice.id, "create_from_jobcard")
    return invoice

@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices(current_user: User = Depends(get_current_user)):
    invoices = await db.invoices.find({"is_deleted": False}, {"_id": 0}).sort("date", -1).to_list(1000)
    return invoices

@api_router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str, current_user: User = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id, "is_deleted": False}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return Invoice(**invoice)

@api_router.patch("/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, update_data: dict, current_user: User = Depends(get_current_user)):
    existing = await db.invoices.find_one({"id": invoice_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # CRITICAL: Only allow editing draft invoices - finalized invoices are immutable
    if existing.get("status") == "finalized":
        raise HTTPException(
            status_code=400, 
            detail="Cannot edit finalized invoice. Finalized invoices are immutable to maintain financial integrity."
        )
    
    # Prevent changing status through this endpoint - use /finalize endpoint instead
    if "status" in update_data:
        del update_data["status"]
    if "finalized_at" in update_data:
        del update_data["finalized_at"]
    if "finalized_by" in update_data:
        del update_data["finalized_by"]
    
    await db.invoices.update_one({"id": invoice_id}, {"$set": update_data})
    await create_audit_log(current_user.id, current_user.full_name, "invoice", invoice_id, "update", update_data)
    return {"message": "Invoice updated successfully"}


@api_router.post("/invoices/{invoice_id}/finalize")
async def finalize_invoice(invoice_id: str, current_user: User = Depends(get_current_user)):
    """
    Finalize a draft invoice - this is when all financial operations happen atomically.
    Once finalized, the invoice becomes immutable to maintain financial integrity.
    
    Atomic operations performed:
    1. Update invoice status to "finalized"
    2. Create Stock OUT movements for all items
    3. Lock linked job card (if exists)
    4. Create customer ledger entry
    5. Update customer outstanding balance
    """
    # Fetch the invoice
    existing = await db.invoices.find_one({"id": invoice_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Validate invoice is in draft state
    current_status = existing.get("status", "draft")
    if current_status == "finalized":
        raise HTTPException(
            status_code=400, 
            detail="Invoice is already finalized"
        )
    
    # Parse invoice data
    invoice = Invoice(**decimal_to_float(existing))
    
    # ATOMIC OPERATION: Finalize invoice with all required operations
    finalized_at = datetime.now(timezone.utc)
    
    # Step 1: Update invoice to finalized status
    await db.invoices.update_one(
        {"id": invoice_id},
        {
            "$set": {
                "status": "finalized",
                "finalized_at": finalized_at,
                "finalized_by": current_user.id
            }
        }
    )
    
    # Step 2: DIRECTLY REDUCE from inventory headers and create audit trail
    stock_errors = []
    for item in invoice.items:
        if item.weight > 0 and item.category:
            # Find the inventory header by category name
            header = await db.inventory_headers.find_one(
                {"name": item.category, "is_deleted": False}, 
                {"_id": 0}
            )
            
            if header:
                # Calculate new stock values
                current_qty = header.get('current_qty', 0)
                current_weight = header.get('current_weight', 0)
                new_qty = current_qty - item.qty
                new_weight = current_weight - item.weight
                
                # Check for insufficient stock
                if new_qty < 0 or new_weight < 0:
                    stock_errors.append(
                        f"{item.category}: Need {item.qty} qty/{item.weight}g, but only {current_qty} qty/{current_weight}g available"
                    )
                    continue
                
                # DIRECT UPDATE: Reduce from inventory header
                await db.inventory_headers.update_one(
                    {"id": header['id']},
                    {"$set": {"current_qty": new_qty, "current_weight": new_weight}}
                )
                
                # Create stock movement for audit trail
                movement = StockMovement(
                    movement_type="Stock OUT",
                    header_id=header['id'],
                    header_name=header['name'],
                    description=f"Invoice {invoice.invoice_number} - Finalized",
                    qty_delta=-item.qty,
                    weight_delta=-item.weight,
                    purity=item.purity,
                    reference_type="invoice",
                    reference_id=invoice.id,
                    created_by=current_user.id
                )
                await db.stock_movements.insert_one(movement.model_dump())
    
    # If there were stock errors, rollback the invoice finalization
    if stock_errors:
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"status": "draft", "finalized_at": None, "finalized_by": None}}
        )
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock: {'; '.join(stock_errors)}"
        )
    
    # Step 3: Lock the linked job card (make it read-only)
    if invoice.jobcard_id:
        jobcard = await db.jobcards.find_one({"id": invoice.jobcard_id, "is_deleted": False})
        if jobcard:
            await db.jobcards.update_one(
                {"id": invoice.jobcard_id},
                {
                    "$set": {
                        "status": "invoiced",
                        "locked": True,
                        "locked_at": finalized_at,
                        "locked_by": current_user.id
                    }
                }
            )
            await create_audit_log(
                current_user.id,
                current_user.full_name,
                "jobcard",
                invoice.jobcard_id,
                "lock",
                {"locked": True, "reason": f"Invoice {invoice.invoice_number} finalized"}
            )
    
    # Step 4: Create customer ledger entry (Transaction)
    if invoice.customer_id and invoice.grand_total > 0:
        # Generate transaction number
        year = datetime.now(timezone.utc).year
        count = await db.transactions.count_documents({"transaction_number": {"$regex": f"^TXN-{year}"}})
        transaction_number = f"TXN-{year}-{str(count + 1).zfill(4)}"
        
        # Get or create a default sales account
        sales_account = await db.accounts.find_one({"name": "Sales"})
        if not sales_account:
            # Create default sales account if it doesn't exist
            default_account = {
                "id": str(uuid.uuid4()),
                "name": "Sales",
                "account_type": "asset",
                "opening_balance": 0,
                "current_balance": 0,
                "created_by": current_user.id,
                "created_at": finalized_at,
                "is_deleted": False
            }
            await db.accounts.insert_one(default_account)
            sales_account = default_account
        
        # Determine transaction type based on invoice type
        # For sales and service invoices, customer owes money (debit to customer account)
        # For purchase invoices, we owe money (credit to supplier account)
        transaction_type = "debit" if invoice.invoice_type in ["sale", "service"] else "credit"
        
        # Create ledger entry as a transaction
        ledger_entry = Transaction(
            transaction_number=transaction_number,
            transaction_type=transaction_type,
            mode="invoice",
            account_id=sales_account["id"],
            account_name=sales_account["name"],
            party_id=invoice.customer_id,
            party_name=invoice.customer_name or "Unknown Customer",
            amount=invoice.grand_total,
            category="Sales Invoice",
            notes=f"Invoice {invoice.invoice_number} finalized",
            created_by=current_user.id
        )
        await db.transactions.insert_one(ledger_entry.model_dump())
        
        await create_audit_log(
            current_user.id,
            current_user.full_name,
            "transaction",
            ledger_entry.id,
            "create",
            {"invoice_id": invoice.id, "amount": invoice.grand_total}
        )
    
    # Step 5: Outstanding balance is automatically updated
    # The balance_due field in the invoice record already tracks outstanding amount
    # Party ledger calculations aggregate all invoice balance_due values
    
    # Create audit log for finalization
    await create_audit_log(
        current_user.id, 
        current_user.full_name, 
        "invoice", 
        invoice.id, 
        "finalize", 
        {
            "status": "finalized", 
            "finalized_at": finalized_at.isoformat(),
            "jobcard_locked": bool(invoice.jobcard_id),
            "ledger_entry_created": bool(invoice.customer_id and invoice.grand_total > 0)
        }
    )
    
    # Fetch and return updated invoice
    updated_invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    return decimal_to_float(updated_invoice)

@api_router.post("/invoices/{invoice_id}/add-payment")
async def add_payment_to_invoice(
    invoice_id: str, 
    payment_data: dict, 
    current_user: User = Depends(get_current_user)
):
    """
    Add payment to an invoice and create a transaction record.
    
    Required fields in payment_data:
    - amount: float
    - payment_mode: str (Cash, Bank Transfer, Card, UPI/Online, Cheque)
    - account_id: str (which account receives the payment)
    - notes: Optional[str]
    
    For walk-in customers: Recommend full payment but allow partial
    For saved customers: Allow partial payments (outstanding tracked in ledger)
    """
    # Validate required fields
    if not payment_data.get('amount') or payment_data['amount'] <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than 0")
    
    if not payment_data.get('payment_mode'):
        raise HTTPException(status_code=400, detail="Payment mode is required")
    
    if not payment_data.get('account_id'):
        raise HTTPException(status_code=400, detail="Account ID is required")
    
    # Fetch invoice
    existing = await db.invoices.find_one({"id": invoice_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice = Invoice(**decimal_to_float(existing))
    
    # Calculate new paid amount and balance
    payment_amount = float(payment_data['amount'])
    new_paid_amount = invoice.paid_amount + payment_amount
    new_balance_due = invoice.grand_total - new_paid_amount
    
    # Validate payment doesn't exceed balance
    if new_balance_due < -0.01:  # Allow small rounding errors
        raise HTTPException(
            status_code=400, 
            detail=f"Payment amount ({payment_amount}) exceeds remaining balance ({invoice.balance_due})"
        )
    
    # Fetch account
    account = await db.accounts.find_one({"id": payment_data['account_id'], "is_deleted": False}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Determine party details based on customer type
    party_id = None
    party_name = ""
    
    if invoice.customer_type == "saved":
        party_id = invoice.customer_id
        party_name = invoice.customer_name or "Unknown Customer"
    else:  # walk_in
        party_id = None
        party_name = f"{invoice.walk_in_name or 'Walk-in Customer'} (Walk-in)"
    
    # Generate transaction number
    year = datetime.now(timezone.utc).year
    count = await db.transactions.count_documents({"transaction_number": {"$regex": f"^TXN-{year}"}})
    transaction_number = f"TXN-{year}-{str(count + 1).zfill(4)}"
    
    # Create transaction record
    transaction = Transaction(
        transaction_number=transaction_number,
        transaction_type="credit",  # Money coming in
        mode=payment_data['payment_mode'],
        account_id=payment_data['account_id'],
        account_name=account['name'],
        party_id=party_id,
        party_name=party_name,
        amount=payment_amount,
        category="Invoice Payment",
        notes=f"Payment for {invoice.invoice_number}. {payment_data.get('notes', '')}".strip(),
        created_by=current_user.id
    )
    
    # Insert transaction
    await db.transactions.insert_one(transaction.model_dump())
    
    # Update invoice payment details
    new_payment_status = "paid" if new_balance_due < 0.01 else "partial"
    await db.invoices.update_one(
        {"id": invoice_id},
        {
            "$set": {
                "paid_amount": new_paid_amount,
                "balance_due": max(0, new_balance_due),  # Ensure no negative balance
                "payment_status": new_payment_status
            }
        }
    )
    
    # Create audit logs
    await create_audit_log(
        current_user.id,
        current_user.full_name,
        "transaction",
        transaction.id,
        "create",
        {"invoice_id": invoice_id, "payment_amount": payment_amount}
    )
    
    await create_audit_log(
        current_user.id,
        current_user.full_name,
        "invoice",
        invoice_id,
        "add_payment",
        {
            "amount": payment_amount,
            "new_paid_amount": new_paid_amount,
            "new_balance_due": max(0, new_balance_due),
            "payment_mode": payment_data['payment_mode']
        }
    )
    
    # Return success response with updated invoice details
    return {
        "message": "Payment added successfully",
        "transaction_id": transaction.id,
        "transaction_number": transaction_number,
        "new_paid_amount": new_paid_amount,
        "new_balance_due": max(0, new_balance_due),
        "payment_status": new_payment_status,
        "is_walk_in_partial_payment": invoice.customer_type == "walk_in" and new_balance_due > 0.01
    }


@api_router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str, current_user: User = Depends(get_current_user)):
    existing = await db.invoices.find_one({"id": invoice_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # CRITICAL: Only allow deleting draft invoices
    # Finalized invoices should not be deleted to maintain financial integrity
    if existing.get("status") == "finalized":
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete finalized invoice. Finalized invoices are immutable to maintain financial integrity."
        )
    
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {"is_deleted": True}}
    )
    await create_audit_log(current_user.id, current_user.full_name, "invoice", invoice_id, "delete")
    return {"message": "Invoice deleted successfully"}

@api_router.get("/invoices/{invoice_id}/pdf")
async def generate_invoice_pdf(invoice_id: str, current_user: User = Depends(get_current_user)):
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    
    invoice = await db.invoices.find_one({"id": invoice_id, "is_deleted": False}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, "Gold Shop ERP")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, "The Artisan Ledger")
    
    # Invoice details
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 120, f"Invoice #{invoice.get('invoice_number', '')}")
    p.setFont("Helvetica", 10)
    invoice_date = invoice.get('date', '')
    if isinstance(invoice_date, str):
        date_str = invoice_date[:10]
    else:
        date_str = str(invoice_date)[:10]
    p.drawString(50, height - 140, f"Date: {date_str}")
    p.drawString(50, height - 155, f"Customer: {invoice.get('customer_name', 'N/A')}")
    p.drawString(50, height - 170, f"Type: {invoice.get('invoice_type', 'sale').upper()}")
    p.drawString(50, height - 185, f"Status: {invoice.get('payment_status', 'unpaid').upper()}")
    
    # Items table
    y_position = height - 230
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y_position, "Item")
    p.drawString(250, y_position, "Qty")
    p.drawString(300, y_position, "Weight")
    p.drawString(370, y_position, "Rate")
    p.drawString(450, y_position, "Total")
    
    p.setFont("Helvetica", 9)
    y_position -= 20
    
    for item in invoice.get('items', []):
        p.drawString(50, y_position, item.get('description', '')[:30])
        p.drawString(250, y_position, str(item.get('qty', 0)))
        p.drawString(300, y_position, f"{item.get('weight', 0)}g")
        p.drawString(370, y_position, f"{item.get('metal_rate', 0):.2f}")
        p.drawString(450, y_position, f"{item.get('line_total', 0):.2f}")
        y_position -= 15
        
        if y_position < 100:
            p.showPage()
            y_position = height - 50
    
    # Totals
    y_position -= 20
    p.setFont("Helvetica-Bold", 10)
    p.drawString(370, y_position, "Subtotal:")
    p.drawString(450, y_position, f"{invoice.get('subtotal', 0):.2f} OMR")
    y_position -= 15
    p.drawString(370, y_position, "VAT:")
    p.drawString(450, y_position, f"{invoice.get('vat_total', 0):.2f} OMR")
    y_position -= 15
    p.setFont("Helvetica-Bold", 12)
    p.drawString(370, y_position, "Grand Total:")
    p.drawString(450, y_position, f"{invoice.get('grand_total', 0):.2f} OMR")
    y_position -= 15
    p.setFont("Helvetica", 10)
    p.drawString(370, y_position, "Balance Due:")
    p.drawString(450, y_position, f"{invoice.get('balance_due', 0):.2f} OMR")
    
    # Footer
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(50, 50, "Thank you for your business!")
    
    p.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{invoice.get('invoice_number', 'unknown')}.pdf"}
    )

@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_data: dict, current_user: User = Depends(get_current_user)):
    year = datetime.now(timezone.utc).year
    count = await db.invoices.count_documents({"invoice_number": {"$regex": f"^INV-{year}"}})
    invoice_number = f"INV-{year}-{str(count + 1).zfill(4)}"
    
    # Create invoice in draft status - NO stock deduction happens here
    invoice = Invoice(**invoice_data, invoice_number=invoice_number, created_by=current_user.id)
    await db.invoices.insert_one(invoice.model_dump())
    
    # Stock movements will ONLY happen when invoice is finalized via /invoices/{id}/finalize endpoint
    
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

@api_router.patch("/accounts/{account_id}")
async def update_account(account_id: str, update_data: dict, current_user: User = Depends(get_current_user)):
    existing = await db.accounts.find_one({"id": account_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="Account not found")
    
    await db.accounts.update_one({"id": account_id}, {"$set": update_data})
    await create_audit_log(current_user.id, current_user.full_name, "account", account_id, "update", update_data)
    return {"message": "Account updated successfully"}

@api_router.delete("/accounts/{account_id}")
async def delete_account(account_id: str, current_user: User = Depends(get_current_user)):
    existing = await db.accounts.find_one({"id": account_id, "is_deleted": False})
    if not existing:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check if account has transactions
    transactions = await db.transactions.find_one({"account_id": account_id, "is_deleted": False})
    if transactions:
        raise HTTPException(status_code=400, detail="Cannot delete account with existing transactions")
    
    await db.accounts.update_one(
        {"id": account_id},
        {"$set": {"is_deleted": True}}
    )
    await create_audit_log(current_user.id, current_user.full_name, "account", account_id, "delete")
    return {"message": "Account deleted successfully"}

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

@api_router.get("/reports/inventory-export")
async def export_inventory(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    movement_type: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    
    # Build query with filters
    query = {"is_deleted": False}
    if start_date:
        query['date'] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        if 'date' in query:
            query['date']['$lte'] = end_dt
        else:
            query['date'] = {"$lte": end_dt}
    if movement_type:
        query['movement_type'] = movement_type
    if category:
        query['header_name'] = category
    
    # Get filtered inventory data
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("date", -1).to_list(10000)
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inventory Movements"
    
    # Headers
    headers = ["Date", "Type", "Category", "Description", "Quantity", "Weight (g)", "Purity", "Notes"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(horizontal="center")
    
    # Data
    for row_idx, movement in enumerate(movements, 2):
        ws.cell(row=row_idx, column=1, value=str(movement.get('date', ''))[:10])
        ws.cell(row=row_idx, column=2, value=movement.get('movement_type', ''))
        ws.cell(row=row_idx, column=3, value=movement.get('header_name', ''))
        ws.cell(row=row_idx, column=4, value=movement.get('description', ''))
        ws.cell(row=row_idx, column=5, value=movement.get('qty_delta', 0))
        ws.cell(row=row_idx, column=6, value=movement.get('weight_delta', 0))
        ws.cell(row=row_idx, column=7, value=movement.get('purity', 0))
        ws.cell(row=row_idx, column=8, value=movement.get('notes', ''))
    
    # Adjust column widths
    for col in range(1, 9):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventory_export.xlsx"}
    )

@api_router.get("/reports/parties-export")
async def export_parties(
    party_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    
    # Build query with filters
    query = {"is_deleted": False}
    if party_type:
        query['party_type'] = party_type
    
    parties = await db.parties.find(query, {"_id": 0}).to_list(10000)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Parties"
    
    headers = ["Name", "Phone", "Type", "Address", "Notes", "Created At"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    
    for row_idx, party in enumerate(parties, 2):
        ws.cell(row=row_idx, column=1, value=party.get('name', ''))
        ws.cell(row=row_idx, column=2, value=party.get('phone', ''))
        ws.cell(row=row_idx, column=3, value=party.get('party_type', ''))
        ws.cell(row=row_idx, column=4, value=party.get('address', ''))
        ws.cell(row=row_idx, column=5, value=party.get('notes', ''))
        ws.cell(row=row_idx, column=6, value=str(party.get('created_at', ''))[:10])
    
    for col in range(1, 7):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 20
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=parties_export.xlsx"}
    )

@api_router.get("/reports/invoices-export")
async def export_invoices(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    invoice_type: Optional[str] = None,
    payment_status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    
    # Build query with filters
    query = {"is_deleted": False}
    if start_date:
        query['date'] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        if 'date' in query:
            query['date']['$lte'] = end_dt
        else:
            query['date'] = {"$lte": end_dt}
    if invoice_type:
        query['invoice_type'] = invoice_type
    if payment_status:
        query['payment_status'] = payment_status
    
    invoices = await db.invoices.find(query, {"_id": 0}).sort("date", -1).to_list(10000)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Invoices"
    
    headers = ["Invoice #", "Date", "Customer", "Type", "Grand Total", "Paid", "Balance", "Status"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    
    for row_idx, inv in enumerate(invoices, 2):
        ws.cell(row=row_idx, column=1, value=inv.get('invoice_number', ''))
        ws.cell(row=row_idx, column=2, value=str(inv.get('date', ''))[:10])
        ws.cell(row=row_idx, column=3, value=inv.get('customer_name', ''))
        ws.cell(row=row_idx, column=4, value=inv.get('invoice_type', ''))
        ws.cell(row=row_idx, column=5, value=inv.get('grand_total', 0))
        ws.cell(row=row_idx, column=6, value=inv.get('paid_amount', 0))
        ws.cell(row=row_idx, column=7, value=inv.get('balance_due', 0))
        ws.cell(row=row_idx, column=8, value=inv.get('payment_status', ''))
    
    for col in range(1, 9):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 18
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=invoices_export.xlsx"}
    )

# New VIEW endpoints for displaying reports in UI
@api_router.get("/reports/inventory-view")
async def view_inventory_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    movement_type: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: Optional[str] = None,  # NEW: "date_asc", "date_desc"
    current_user: User = Depends(get_current_user)
):
    """View inventory movements with filters - returns JSON for UI"""
    query = {"is_deleted": False}
    if start_date:
        query['date'] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        if 'date' in query:
            query['date']['$lte'] = end_dt
        else:
            query['date'] = {"$lte": end_dt}
    if movement_type:
        query['movement_type'] = movement_type
    if category:
        query['header_name'] = category
    
    # Apply sorting
    sort_field = "date"
    sort_direction = -1  # Default: newest first
    
    if sort_by == "date_asc":
        sort_direction = 1
    elif sort_by == "date_desc":
        sort_direction = -1
    
    movements = await db.stock_movements.find(query, {"_id": 0}).sort(sort_field, sort_direction).to_list(10000)
    
    # Calculate totals
    total_in = sum(m.get('qty_delta', 0) for m in movements if m.get('qty_delta', 0) > 0)
    total_out = sum(abs(m.get('qty_delta', 0)) for m in movements if m.get('qty_delta', 0) < 0)
    total_weight_in = sum(m.get('weight_delta', 0) for m in movements if m.get('weight_delta', 0) > 0)
    total_weight_out = sum(abs(m.get('weight_delta', 0)) for m in movements if m.get('weight_delta', 0) < 0)
    
    return {
        "movements": movements,
        "summary": {
            "total_in": total_in,
            "total_out": total_out,
            "total_weight_in": total_weight_in,
            "total_weight_out": total_weight_out,
            "net_quantity": total_in - total_out,
            "net_weight": total_weight_in - total_weight_out
        },
        "count": len(movements)
    }

@api_router.get("/reports/parties-view")
async def view_parties_report(
    party_type: Optional[str] = None,
    sort_by: Optional[str] = None,  # NEW: "outstanding_desc", "name_asc"
    current_user: User = Depends(get_current_user)
):
    """View parties with filters - returns JSON for UI"""
    query = {"is_deleted": False}
    if party_type:
        query['party_type'] = party_type
    
    parties = await db.parties.find(query, {"_id": 0}).to_list(10000)
    
    # Get outstanding amounts for each party
    for party in parties:
        invoices = await db.invoices.find(
            {"customer_id": party['id'], "is_deleted": False},
            {"_id": 0, "balance_due": 1}
        ).to_list(1000)
        party['outstanding'] = sum(inv.get('balance_due', 0) for inv in invoices)
    
    # Apply sorting
    if sort_by == "outstanding_desc":
        parties = sorted(parties, key=lambda x: x.get('outstanding', 0), reverse=True)
    elif sort_by == "name_asc":
        parties = sorted(parties, key=lambda x: x.get('name', '').lower())
    
    return {
        "parties": parties,
        "count": len(parties)
    }

@api_router.get("/reports/invoices-view")
async def view_invoices_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    invoice_type: Optional[str] = None,
    payment_status: Optional[str] = None,
    party_id: Optional[str] = None,  # NEW: Filter by specific party
    sort_by: Optional[str] = None,  # NEW: "date_asc", "date_desc", "amount_desc", "outstanding_desc"
    current_user: User = Depends(get_current_user)
):
    """View invoices with filters - returns JSON for UI"""
    query = {"is_deleted": False}
    if start_date:
        query['date'] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        if 'date' in query:
            query['date']['$lte'] = end_dt
        else:
            query['date'] = {"$lte": end_dt}
    if invoice_type:
        query['invoice_type'] = invoice_type
    if payment_status:
        query['payment_status'] = payment_status
    if party_id:
        query['customer_id'] = party_id
    
    # Apply sorting
    sort_field = "date"
    sort_direction = -1  # Default: newest first
    
    if sort_by == "date_asc":
        sort_field = "date"
        sort_direction = 1
    elif sort_by == "date_desc":
        sort_field = "date"
        sort_direction = -1
    elif sort_by == "amount_desc":
        sort_field = "grand_total"
        sort_direction = -1
    elif sort_by == "outstanding_desc":
        sort_field = "balance_due"
        sort_direction = -1
    
    invoices = await db.invoices.find(query, {"_id": 0}).sort(sort_field, sort_direction).to_list(10000)
    
    # Calculate totals
    total_amount = sum(inv.get('grand_total', 0) for inv in invoices)
    total_paid = sum(inv.get('paid_amount', 0) for inv in invoices)
    total_balance = sum(inv.get('balance_due', 0) for inv in invoices)
    
    return {
        "invoices": invoices,
        "summary": {
            "total_amount": total_amount,
            "total_paid": total_paid,
            "total_balance": total_balance
        },
        "count": len(invoices)
    }

@api_router.get("/reports/transactions-view")
async def view_transactions_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[str] = None,
    account_id: Optional[str] = None,
    party_id: Optional[str] = None,  # NEW: Filter by specific party
    sort_by: Optional[str] = None,  # NEW: "date_asc", "date_desc", "amount_desc"
    current_user: User = Depends(get_current_user)
):
    """View financial transactions with filters - returns JSON for UI"""
    query = {"is_deleted": False}
    if start_date:
        query['date'] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        if 'date' in query:
            query['date']['$lte'] = end_dt
        else:
            query['date'] = {"$lte": end_dt}
    if transaction_type:
        query['transaction_type'] = transaction_type
    if account_id:
        query['account_id'] = account_id
    if party_id:
        query['party_id'] = party_id
    
    # Apply sorting
    sort_field = "date"
    sort_direction = -1  # Default: newest first
    
    if sort_by == "date_asc":
        sort_field = "date"
        sort_direction = 1
    elif sort_by == "date_desc":
        sort_field = "date"
        sort_direction = -1
    elif sort_by == "amount_desc":
        sort_field = "amount"
        sort_direction = -1
    
    transactions = await db.transactions.find(query, {"_id": 0}).sort(sort_field, sort_direction).to_list(10000)
    
    # Calculate totals
    total_credit = sum(txn.get('amount', 0) for txn in transactions if txn.get('transaction_type') == 'credit')
    total_debit = sum(txn.get('amount', 0) for txn in transactions if txn.get('transaction_type') == 'debit')
    
    return {
        "transactions": transactions,
        "summary": {
            "total_credit": total_credit,
            "total_debit": total_debit,
            "net_balance": total_credit - total_debit
        },
        "count": len(transactions)
    }

@api_router.get("/reports/invoice/{invoice_id}")
async def get_invoice_report(invoice_id: str, current_user: User = Depends(get_current_user)):
    """Get detailed report for a single invoice"""
    invoice = await db.invoices.find_one({"id": invoice_id, "is_deleted": False}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get related payments/transactions
    transactions = await db.transactions.find(
        {"party_id": invoice.get('customer_id'), "is_deleted": False},
        {"_id": 0}
    ).to_list(1000)
    
    return {
        "invoice": invoice,
        "transactions": transactions
    }

@api_router.get("/reports/party/{party_id}/ledger-report")
async def get_party_ledger_report(
    party_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get detailed ledger report for a party with date filtering"""
    party = await db.parties.find_one({"id": party_id, "is_deleted": False}, {"_id": 0})
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    
    # Build query for invoices
    invoice_query = {"customer_id": party_id, "is_deleted": False}
    if start_date:
        invoice_query['date'] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        if 'date' in invoice_query:
            invoice_query['date']['$lte'] = end_dt
        else:
            invoice_query['date'] = {"$lte": end_dt}
    
    invoices = await db.invoices.find(invoice_query, {"_id": 0}).sort("date", -1).to_list(1000)
    
    # Build query for transactions
    txn_query = {"party_id": party_id, "is_deleted": False}
    if start_date:
        txn_query['date'] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        if 'date' in txn_query:
            txn_query['date']['$lte'] = end_dt
        else:
            txn_query['date'] = {"$lte": end_dt}
    
    transactions = await db.transactions.find(txn_query, {"_id": 0}).sort("date", -1).to_list(1000)
    
    # Calculate totals
    total_invoiced = sum(inv.get('grand_total', 0) for inv in invoices)
    total_paid = sum(txn.get('amount', 0) for txn in transactions if txn.get('transaction_type') == 'debit')
    total_outstanding = sum(inv.get('balance_due', 0) for inv in invoices)
    
    return {
        "party": party,
        "invoices": invoices,
        "transactions": transactions,
        "summary": {
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding
        }
    }

@api_router.get("/reports/inventory/{header_id}/stock-report")
async def get_inventory_stock_report(
    header_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get detailed stock report for a specific inventory category"""
    header = await db.inventory_headers.find_one({"id": header_id, "is_deleted": False}, {"_id": 0})
    if not header:
        raise HTTPException(status_code=404, detail="Inventory category not found")
    
    # Build query for movements
    query = {"header_id": header_id, "is_deleted": False}
    if start_date:
        query['date'] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        if 'date' in query:
            query['date']['$lte'] = end_dt
        else:
            query['date'] = {"$lte": end_dt}
    
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("date", -1).to_list(10000)
    
    # Calculate stock totals
    total_in = sum(m.get('qty_delta', 0) for m in movements if m.get('qty_delta', 0) > 0)
    total_out = sum(abs(m.get('qty_delta', 0)) for m in movements if m.get('qty_delta', 0) < 0)
    current_stock = total_in - total_out
    
    total_weight_in = sum(m.get('weight_delta', 0) for m in movements if m.get('weight_delta', 0) > 0)
    total_weight_out = sum(abs(m.get('weight_delta', 0)) for m in movements if m.get('weight_delta', 0) < 0)
    current_weight = total_weight_in - total_weight_out
    
    return {
        "header": header,
        "movements": movements,
        "summary": {
            "total_in": total_in,
            "total_out": total_out,
            "current_stock": current_stock,
            "total_weight_in": total_weight_in,
            "total_weight_out": total_weight_out,
            "current_weight": current_weight
        },
        "count": len(movements)
    }

@api_router.get("/reports/financial-summary")
async def get_financial_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get financial summary with optional date filtering"""
    # Build query for invoices
    invoice_query = {"is_deleted": False}
    if start_date:
        invoice_query['date'] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        if 'date' in invoice_query:
            invoice_query['date']['$lte'] = end_dt
        else:
            invoice_query['date'] = {"$lte": end_dt}
    
    # Build query for transactions
    txn_query = {"is_deleted": False}
    if start_date:
        txn_query['date'] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        if 'date' in txn_query:
            txn_query['date']['$lte'] = end_dt
        else:
            txn_query['date'] = {"$lte": end_dt}
    
    # Get totals for financial summary
    invoices = await db.invoices.find(invoice_query, {"_id": 0}).to_list(10000)
    transactions = await db.transactions.find(txn_query, {"_id": 0}).to_list(10000)
    accounts = await db.accounts.find({"is_deleted": False}, {"_id": 0}).to_list(1000)
    
    total_sales = sum(inv.get('grand_total', 0) for inv in invoices if inv.get('invoice_type') == 'sale')
    total_purchases = sum(inv.get('grand_total', 0) for inv in invoices if inv.get('invoice_type') == 'purchase')
    total_outstanding = sum(inv.get('balance_due', 0) for inv in invoices)
    
    total_credit = sum(txn.get('amount', 0) for txn in transactions if txn.get('transaction_type') == 'credit')
    total_debit = sum(txn.get('amount', 0) for txn in transactions if txn.get('transaction_type') == 'debit')
    
    total_account_balance = sum(acc.get('current_balance', 0) for acc in accounts)
    
    # NEW: Calculate cash and bank balances separately
    cash_balance = sum(acc.get('current_balance', 0) for acc in accounts 
                      if 'cash' in acc.get('account_type', '').lower())
    bank_balance = sum(acc.get('current_balance', 0) for acc in accounts 
                      if 'bank' in acc.get('account_type', '').lower())
    
    # NEW: Calculate net flow
    net_flow = total_credit - total_debit
    
    # NEW: Get daily closing difference for today (or selected date range)
    daily_closing_difference = 0
    closing_query = {"is_deleted": False}
    if start_date and end_date:
        # If date range provided, get all closings in range
        closing_query['date'] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    else:
        # Default to today
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        closing_query['date'] = {"$gte": today}
    
    closings = await db.daily_closings.find(closing_query, {"_id": 0}).to_list(100)
    for closing in closings:
        expected = closing.get('expected_closing', 0)
        actual = closing.get('actual_closing', 0)
        daily_closing_difference += (actual - expected)
    
    return {
        "total_sales": total_sales,
        "total_purchases": total_purchases,
        "total_outstanding": total_outstanding,
        "total_credit": total_credit,
        "total_debit": total_debit,
        "total_account_balance": total_account_balance,
        "cash_balance": cash_balance,
        "bank_balance": bank_balance,
        "net_flow": net_flow,
        "daily_closing_difference": daily_closing_difference,
        "net_profit": total_sales - total_purchases
    }


@api_router.get("/reports/outstanding")
async def get_outstanding_report(
    party_id: Optional[str] = None,
    party_type: Optional[str] = None,  # "customer", "vendor", or None for both
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_paid: bool = False,  # Include fully paid invoices
    current_user: User = Depends(get_current_user)
):
    """
    Get outstanding report with overdue buckets
    Shows total invoiced, paid, outstanding per party
    Includes overdue buckets: 0-7, 8-30, 31+ days
    """
    # Build invoice query
    invoice_query = {"is_deleted": False, "status": "finalized"}
    
    if not include_paid:
        # Only include invoices with outstanding balance
        invoice_query['balance_due'] = {"$gt": 0}
    
    if start_date:
        invoice_query['date'] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        if 'date' in invoice_query:
            invoice_query['date']['$lte'] = end_dt
        else:
            invoice_query['date'] = {"$lte": end_dt}
    
    # Get all invoices
    invoices = await db.invoices.find(invoice_query, {"_id": 0}).to_list(10000)
    
    # Get all transactions for payment tracking
    transactions = await db.transactions.find(
        {"is_deleted": False, "category": {"$in": ["Sales Invoice", "Purchase Invoice"]}},
        {"_id": 0}
    ).to_list(10000)
    
    # Calculate today for overdue calculations
    today = datetime.now(timezone.utc)
    
    # Group by party
    party_data = {}
    
    for inv in invoices:
        # Determine party info
        if inv.get('customer_type') == 'walk_in':
            party_key = f"walk_in_{inv.get('walk_in_name', 'Unknown')}"
            party_name = f"{inv.get('walk_in_name', 'Unknown')} (Walk-in)"
            ptype = "customer"
        elif inv.get('customer_id'):
            party_key = inv['customer_id']
            party_name = inv.get('customer_name', 'Unknown')
            ptype = "customer" if inv.get('invoice_type') == 'sale' else "vendor"
        else:
            continue
        
        # Filter by party_id if specified
        if party_id and party_key != party_id:
            continue
        
        # Filter by party_type if specified
        if party_type and ptype != party_type:
            continue
        
        # Initialize party data
        if party_key not in party_data:
            party_data[party_key] = {
                "party_id": party_key,
                "party_name": party_name,
                "party_type": ptype,
                "total_invoiced": 0,
                "total_paid": 0,
                "total_outstanding": 0,
                "overdue_0_7": 0,
                "overdue_8_30": 0,
                "overdue_31_plus": 0,
                "last_invoice_date": None,
                "last_payment_date": None,
                "invoice_count": 0
            }
        
        # Update totals
        party_data[party_key]['total_invoiced'] += inv.get('grand_total', 0)
        party_data[party_key]['total_paid'] += inv.get('paid_amount', 0)
        party_data[party_key]['total_outstanding'] += inv.get('balance_due', 0)
        party_data[party_key]['invoice_count'] += 1
        
        # Update last invoice date
        inv_date = inv.get('date')
        if inv_date:
            if isinstance(inv_date, str):
                inv_date = datetime.fromisoformat(inv_date)
            if not party_data[party_key]['last_invoice_date'] or inv_date > party_data[party_key]['last_invoice_date']:
                party_data[party_key]['last_invoice_date'] = inv_date
        
        # Calculate overdue only if balance_due > 0
        if inv.get('balance_due', 0) > 0:
            # Use due_date if available, else fallback to invoice date
            due_date = inv.get('due_date') or inv.get('date')
            if due_date:
                if isinstance(due_date, str):
                    due_date = datetime.fromisoformat(due_date)
                
                overdue_days = (today - due_date).days
                
                if overdue_days >= 0:  # Only count if actually overdue
                    outstanding_amount = inv.get('balance_due', 0)
                    if 0 <= overdue_days <= 7:
                        party_data[party_key]['overdue_0_7'] += outstanding_amount
                    elif 8 <= overdue_days <= 30:
                        party_data[party_key]['overdue_8_30'] += outstanding_amount
                    elif overdue_days > 30:
                        party_data[party_key]['overdue_31_plus'] += outstanding_amount
    
    # Get last payment dates from transactions
    for txn in transactions:
        party_key = txn.get('party_id')
        if party_key and party_key in party_data:
            txn_date = txn.get('date')
            if txn_date:
                if isinstance(txn_date, str):
                    txn_date = datetime.fromisoformat(txn_date)
                if not party_data[party_key]['last_payment_date'] or txn_date > party_data[party_key]['last_payment_date']:
                    party_data[party_key]['last_payment_date'] = txn_date
    
    # Convert dates to ISO strings for JSON serialization
    for party in party_data.values():
        if party['last_invoice_date']:
            party['last_invoice_date'] = party['last_invoice_date'].isoformat()
        if party['last_payment_date']:
            party['last_payment_date'] = party['last_payment_date'].isoformat()
    
    # Calculate summary totals
    customer_due = sum(p['total_outstanding'] for p in party_data.values() if p['party_type'] == 'customer')
    vendor_payable = sum(p['total_outstanding'] for p in party_data.values() if p['party_type'] == 'vendor')
    total_outstanding = customer_due + vendor_payable
    
    total_overdue_0_7 = sum(p['overdue_0_7'] for p in party_data.values())
    total_overdue_8_30 = sum(p['overdue_8_30'] for p in party_data.values())
    total_overdue_31_plus = sum(p['overdue_31_plus'] for p in party_data.values())
    
    return {
        "summary": {
            "customer_due": customer_due,
            "vendor_payable": vendor_payable,
            "total_outstanding": total_outstanding,
            "total_overdue_0_7": total_overdue_0_7,
            "total_overdue_8_30": total_overdue_8_30,
            "total_overdue_31_plus": total_overdue_31_plus
        },
        "parties": list(party_data.values())
    }


# ==================== PDF EXPORT ENDPOINTS ====================

@api_router.get("/reports/outstanding-pdf")
async def export_outstanding_pdf(
    party_id: Optional[str] = None,
    party_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Export outstanding report as PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    # Get data from outstanding report
    params = {}
    if party_id:
        params['party_id'] = party_id
    if party_type:
        params['party_type'] = party_type
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    # Call outstanding report endpoint logic
    from urllib.parse import urlencode
    import httpx
    
    # Get outstanding data by calling the endpoint function directly
    data = await get_outstanding_report(
        party_id=party_id,
        party_type=party_type,
        start_date=start_date,
        end_date=end_date,
        include_paid=False,
        current_user=current_user
    )
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, height - inch, "Outstanding Report")
    
    # Date range
    c.setFont("Helvetica", 10)
    date_str = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if start_date or end_date:
        date_str += f" | Period: {start_date or 'Start'} to {end_date or 'End'}"
    c.drawString(inch, height - inch - 0.3*inch, date_str)
    
    # Summary section
    y_position = height - inch - 0.8*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_position, "Summary")
    y_position -= 0.3*inch
    
    c.setFont("Helvetica", 10)
    summary = data['summary']
    c.drawString(inch, y_position, f"Customer Due: {summary['customer_due']:.3f}")
    c.drawString(inch + 2.5*inch, y_position, f"Vendor Payable: {summary['vendor_payable']:.3f}")
    y_position -= 0.2*inch
    c.drawString(inch, y_position, f"Total Outstanding: {summary['total_outstanding']:.3f}")
    y_position -= 0.3*inch
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(inch, y_position, "Overdue Buckets:")
    y_position -= 0.2*inch
    c.setFont("Helvetica", 10)
    c.drawString(inch, y_position, f"0-7 days: {summary['total_overdue_0_7']:.3f}")
    c.drawString(inch + 2*inch, y_position, f"8-30 days: {summary['total_overdue_8_30']:.3f}")
    c.drawString(inch + 4*inch, y_position, f"31+ days: {summary['total_overdue_31_plus']:.3f}")
    y_position -= 0.5*inch
    
    # Parties table
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_position, "Party-wise Outstanding")
    y_position -= 0.3*inch
    
    # Create table data
    table_data = [['Party Name', 'Type', 'Invoiced', 'Paid', 'Outstanding', '0-7d', '8-30d', '31+d']]
    for party in data['parties'][:20]:  # Limit to 20 parties per page
        table_data.append([
            party['party_name'][:25],
            party['party_type'],
            f"{party['total_invoiced']:.2f}",
            f"{party['total_paid']:.2f}",
            f"{party['total_outstanding']:.2f}",
            f"{party['overdue_0_7']:.2f}",
            f"{party['overdue_8_30']:.2f}",
            f"{party['overdue_31_plus']:.2f}"
        ])
    
    # Create table
    table = Table(table_data, colWidths=[2*inch, 0.7*inch, 0.8*inch, 0.8*inch, 0.9*inch, 0.6*inch, 0.7*inch, 0.7*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    # Draw table
    table.wrapOn(c, width, height)
    table.drawOn(c, inch, y_position - len(table_data) * 0.25*inch)
    
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=outstanding_report_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


@api_router.get("/reports/invoices-pdf")
async def export_invoices_pdf(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    invoice_type: Optional[str] = None,
    payment_status: Optional[str] = None,
    party_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Export invoices report as PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    # Get data
    data = await view_invoices_report(
        start_date=start_date,
        end_date=end_date,
        invoice_type=invoice_type,
        payment_status=payment_status,
        party_id=party_id,
        sort_by=None,
        current_user=current_user
    )
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, height - inch, "Invoices Report")
    
    c.setFont("Helvetica", 10)
    date_str = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if start_date or end_date:
        date_str += f" | Period: {start_date or 'Start'} to {end_date or 'End'}"
    c.drawString(inch, height - inch - 0.3*inch, date_str)
    
    # Summary
    y_position = height - inch - 0.8*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_position, "Summary")
    y_position -= 0.3*inch
    
    c.setFont("Helvetica", 10)
    summary = data['summary']
    c.drawString(inch, y_position, f"Total Amount: {summary['total_amount']:.3f}")
    c.drawString(inch + 2.5*inch, y_position, f"Total Paid: {summary['total_paid']:.3f}")
    y_position -= 0.2*inch
    c.drawString(inch, y_position, f"Total Balance: {summary['total_balance']:.3f}")
    c.drawString(inch + 2.5*inch, y_position, f"Count: {data['count']}")
    y_position -= 0.5*inch
    
    # Table
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_position, "Invoices")
    y_position -= 0.3*inch
    
    table_data = [['Invoice #', 'Date', 'Customer', 'Type', 'Amount', 'Paid', 'Balance']]
    for inv in data['invoices'][:25]:
        inv_date = inv.get('date', '')
        if isinstance(inv_date, str):
            inv_date = inv_date[:10]
        elif hasattr(inv_date, 'strftime'):
            inv_date = inv_date.strftime('%Y-%m-%d')
        
        customer = inv.get('customer_name') or inv.get('walk_in_name') or 'N/A'
        table_data.append([
            inv.get('invoice_number', '')[:15],
            inv_date,
            customer[:20],
            inv.get('invoice_type', '')[:4],
            f"{inv.get('grand_total', 0):.2f}",
            f"{inv.get('paid_amount', 0):.2f}",
            f"{inv.get('balance_due', 0):.2f}"
        ])
    
    table = Table(table_data, colWidths=[1.2*inch, 0.9*inch, 1.5*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    table.wrapOn(c, width, height)
    table.drawOn(c, inch, y_position - len(table_data) * 0.25*inch)
    
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoices_report_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


@api_router.get("/reports/parties-pdf")
async def export_parties_pdf(
    party_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Export parties report as PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    # Get data
    data = await view_parties_report(
        party_type=party_type,
        sort_by="outstanding_desc",
        current_user=current_user
    )
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, height - inch, "Parties Report")
    
    c.setFont("Helvetica", 10)
    c.drawString(inch, height - inch - 0.3*inch, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Table
    y_position = height - inch - 0.8*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_position, f"Total Parties: {data['count']}")
    y_position -= 0.4*inch
    
    table_data = [['Party Name', 'Type', 'Phone', 'Email', 'Outstanding']]
    for party in data['parties'][:30]:
        table_data.append([
            party.get('name', '')[:25],
            party.get('party_type', '')[:8],
            party.get('phone', '')[:15],
            party.get('email', '')[:20],
            f"{party.get('outstanding', 0):.2f}"
        ])
    
    table = Table(table_data, colWidths=[2*inch, 0.8*inch, 1.2*inch, 1.5*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    table.wrapOn(c, width, height)
    table.drawOn(c, inch, y_position - len(table_data) * 0.25*inch)
    
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=parties_report_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


@api_router.get("/reports/transactions-pdf")
async def export_transactions_pdf(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[str] = None,
    party_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Export transactions report as PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    # Get data
    data = await view_transactions_report(
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        account_id=None,
        party_id=party_id,
        sort_by=None,
        current_user=current_user
    )
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, height - inch, "Transactions Report")
    
    c.setFont("Helvetica", 10)
    date_str = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if start_date or end_date:
        date_str += f" | Period: {start_date or 'Start'} to {end_date or 'End'}"
    c.drawString(inch, height - inch - 0.3*inch, date_str)
    
    # Summary
    y_position = height - inch - 0.8*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_position, "Summary")
    y_position -= 0.3*inch
    
    c.setFont("Helvetica", 10)
    summary = data['summary']
    c.drawString(inch, y_position, f"Total Credit: {summary['total_credit']:.3f}")
    c.drawString(inch + 2.5*inch, y_position, f"Total Debit: {summary['total_debit']:.3f}")
    y_position -= 0.2*inch
    c.drawString(inch, y_position, f"Net Balance: {summary['net_balance']:.3f}")
    c.drawString(inch + 2.5*inch, y_position, f"Count: {data['count']}")
    y_position -= 0.5*inch
    
    # Table
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_position, "Transactions")
    y_position -= 0.3*inch
    
    table_data = [['TXN #', 'Date', 'Type', 'Account', 'Party', 'Amount']]
    for txn in data['transactions'][:30]:
        txn_date = txn.get('date', '')
        if isinstance(txn_date, str):
            txn_date = txn_date[:10]
        elif hasattr(txn_date, 'strftime'):
            txn_date = txn_date.strftime('%Y-%m-%d')
        
        table_data.append([
            txn.get('transaction_number', '')[:15],
            txn_date,
            txn.get('transaction_type', '')[:6],
            txn.get('account_name', '')[:20],
            txn.get('party_name', 'N/A')[:15],
            f"{txn.get('amount', 0):.2f}"
        ])
    
    table = Table(table_data, colWidths=[1.2*inch, 0.9*inch, 0.7*inch, 1.5*inch, 1.2*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    table.wrapOn(c, width, height)
    table.drawOn(c, inch, y_position - len(table_data) * 0.25*inch)
    
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=transactions_report_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


@api_router.get("/reports/inventory-pdf")
async def export_inventory_pdf(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    movement_type: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Export inventory report as PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    # Get data
    data = await view_inventory_report(
        start_date=start_date,
        end_date=end_date,
        movement_type=movement_type,
        category=category,
        sort_by=None,
        current_user=current_user
    )
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, height - inch, "Inventory Report")
    
    c.setFont("Helvetica", 10)
    date_str = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if start_date or end_date:
        date_str += f" | Period: {start_date or 'Start'} to {end_date or 'End'}"
    c.drawString(inch, height - inch - 0.3*inch, date_str)
    
    # Summary
    y_position = height - inch - 0.8*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_position, "Summary")
    y_position -= 0.3*inch
    
    c.setFont("Helvetica", 10)
    summary = data['summary']
    c.drawString(inch, y_position, f"Total In: {summary['total_in']:.2f} pcs")
    c.drawString(inch + 2.5*inch, y_position, f"Total Out: {summary['total_out']:.2f} pcs")
    y_position -= 0.2*inch
    c.drawString(inch, y_position, f"Weight In: {summary['total_weight_in']:.3f} g")
    c.drawString(inch + 2.5*inch, y_position, f"Weight Out: {summary['total_weight_out']:.3f} g")
    y_position -= 0.5*inch
    
    # Table
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_position, "Stock Movements")
    y_position -= 0.3*inch
    
    table_data = [['Date', 'Category', 'Type', 'Qty', 'Weight', 'Reference']]
    for mov in data['movements'][:30]:
        mov_date = mov.get('date', '')
        if isinstance(mov_date, str):
            mov_date = mov_date[:10]
        elif hasattr(mov_date, 'strftime'):
            mov_date = mov_date.strftime('%Y-%m-%d')
        
        table_data.append([
            mov_date,
            mov.get('header_name', '')[:15],
            mov.get('movement_type', '')[:10],
            f"{mov.get('qty_delta', 0):.1f}",
            f"{mov.get('weight_delta', 0):.2f}",
            mov.get('reference_type', '')[:12]
        ])
    
    table = Table(table_data, colWidths=[0.9*inch, 1.3*inch, 1*inch, 0.7*inch, 0.9*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    table.wrapOn(c, width, height)
    table.drawOn(c, inch, y_position - len(table_data) * 0.25*inch)
    
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=inventory_report_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


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
