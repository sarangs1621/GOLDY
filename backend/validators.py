from pydantic import BaseModel, Field, validator
from typing import Optional
import re
import bleach
import html

class PartyValidator(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    party_type: str = Field(..., pattern="^(customer|vendor|worker)$")
    notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?[\d\s\-()]+$', v):
            raise ValueError('Invalid phone number format')
        return v

class StockMovementValidator(BaseModel):
    movement_type: str = Field(..., pattern="^(Stock IN|Stock OUT|Adjustment IN|Adjustment OUT|Transfer)$")
    header_id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1, max_length=200)
    qty_delta: float = Field(..., ge=-10000, le=10000)
    weight_delta: float = Field(..., ge=-10000, le=10000)
    purity: int = Field(..., ge=1, le=999)
    notes: Optional[str] = Field(None, max_length=500)

class JobCardValidator(BaseModel):
    card_type: str = Field(..., pattern="^(repair|custom|polish|resize)$")
    customer_id: Optional[str] = None
    customer_name: Optional[str] = Field(None, max_length=100)
    worker_id: Optional[str] = None
    worker_name: Optional[str] = Field(None, max_length=100)
    delivery_date: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)

class AccountValidator(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    account_type: str = Field(..., pattern="^(cash|bank|credit_card|mobile_wallet)$")
    opening_balance: float = Field(default=0, ge=-1000000, le=1000000)

class TransactionValidator(BaseModel):
    transaction_type: str = Field(..., pattern="^(credit|debit)$")
    mode: str = Field(..., pattern="^(cash|bank_transfer|card|cheque|online)$")
    account_id: str = Field(..., min_length=1)
    party_id: Optional[str] = None
    party_name: Optional[str] = Field(None, max_length=100)
    amount: float = Field(..., gt=0, le=1000000)
    category: str = Field(..., max_length=50)
    notes: Optional[str] = Field(None, max_length=500)

class UserUpdateValidator(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, pattern="^(admin|manager|staff)$")
    is_active: Optional[bool] = None

class PasswordChangeValidator(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=100)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        return v
