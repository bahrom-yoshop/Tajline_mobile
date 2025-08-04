from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import os
import jwt
import bcrypt
from pymongo import MongoClient
import uuid
from enum import Enum

app = FastAPI()

# CORS настройка
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB подключение
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URL)
db = client.cargo_transport

# JWT настройки
SECRET_KEY = "cargo_transport_secret_key_2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# Enums
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin" 
    WAREHOUSE_OPERATOR = "warehouse_operator"

class CargoStatus(str, Enum):
    CREATED = "created"
    ACCEPTED = "accepted"
    IN_TRANSIT = "in_transit"
    ARRIVED_DESTINATION = "arrived_destination"
    COMPLETED = "completed"

class RouteType(str, Enum):
    MOSCOW_TO_TAJIKISTAN = "moscow_to_tajikistan"
    TAJIKISTAN_TO_MOSCOW = "tajikistan_to_moscow"

# Pydantic модели
class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=10)
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER

class UserLogin(BaseModel):
    phone: str
    password: str

class User(BaseModel):
    id: str
    full_name: str
    phone: str
    role: UserRole
    is_active: bool = True
    created_at: datetime

class CargoCreate(BaseModel):
    recipient_name: str
    recipient_phone: str
    route: RouteType
    weight: float
    description: str
    declared_value: float
    sender_address: str
    recipient_address: str

class Cargo(BaseModel):
    id: str
    cargo_number: str
    sender_id: str
    recipient_name: str
    recipient_phone: str
    route: RouteType
    weight: float
    description: str
    declared_value: float
    sender_address: str
    recipient_address: str
    status: CargoStatus
    created_at: datetime
    updated_at: datetime
    warehouse_location: Optional[str] = None

class NotificationCreate(BaseModel):
    user_id: str
    message: str
    cargo_id: Optional[str] = None

class Notification(BaseModel):
    id: str
    user_id: str
    message: str
    cargo_id: Optional[str] = None
    is_read: bool = False
    created_at: datetime

class WarehouseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    location: str = Field(..., min_length=5, max_length=200)
    blocks_count: int = Field(..., ge=1, le=9)
    shelves_per_block: int = Field(..., ge=1, le=3)
    cells_per_shelf: int = Field(..., ge=1, le=50)

class Warehouse(BaseModel):
    id: str
    name: str
    location: str
    blocks_count: int
    shelves_per_block: int
    cells_per_shelf: int
    total_capacity: int
    created_by: str
    created_at: datetime
    is_active: bool = True

class WarehouseBlock(BaseModel):
    id: str
    warehouse_id: str
    block_number: int
    shelves: List[dict]  # List of shelves with cells

class WarehouseCell(BaseModel):
    id: str
    warehouse_id: str
    block_number: int
    shelf_number: int
    cell_number: int
    is_occupied: bool = False
    cargo_id: Optional[str] = None
    location_code: str  # Format: "B1-S2-C3" (Block 1, Shelf 2, Cell 3)

# Утилиты
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.users.find_one({"phone": phone})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(
            id=user["id"],
            full_name=user["full_name"],
            phone=user["phone"],
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

def generate_cargo_number() -> str:
    return f"CG{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"

def create_notification(user_id: str, message: str, cargo_id: str = None):
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "message": message,
        "cargo_id": cargo_id,
        "is_read": False,
        "created_at": datetime.utcnow()
    }
    db.notifications.insert_one(notification)

# API Routes

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Аутентификация
@app.post("/api/auth/register")
async def register(user_data: UserCreate):
    # Проверка существования пользователя
    if db.users.find_one({"phone": user_data.phone}):
        raise HTTPException(status_code=400, detail="User with this phone already exists")
    
    # Создание пользователя
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "full_name": user_data.full_name,
        "phone": user_data.phone,
        "password": hash_password(user_data.password),
        "role": user_data.role,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    db.users.insert_one(user)
    
    # Создание токена
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.phone}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(
            id=user_id,
            full_name=user_data.full_name,
            phone=user_data.phone,
            role=user_data.role,
            is_active=True,
            created_at=user["created_at"]
        )
    }

@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    user = db.users.find_one({"phone": user_data.phone})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid phone or password")
    
    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.phone}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(
            id=user["id"],
            full_name=user["full_name"],
            phone=user["phone"],
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        )
    }

# Управление грузами
@app.post("/api/cargo/create")
async def create_cargo(cargo_data: CargoCreate, current_user: User = Depends(get_current_user)):
    cargo_id = str(uuid.uuid4())
    cargo_number = generate_cargo_number()
    
    cargo = {
        "id": cargo_id,
        "cargo_number": cargo_number,
        "sender_id": current_user.id,
        "recipient_name": cargo_data.recipient_name,
        "recipient_phone": cargo_data.recipient_phone,
        "route": cargo_data.route,
        "weight": cargo_data.weight,
        "description": cargo_data.description,
        "declared_value": cargo_data.declared_value,
        "sender_address": cargo_data.sender_address,
        "recipient_address": cargo_data.recipient_address,
        "status": CargoStatus.CREATED,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "warehouse_location": None
    }
    
    db.cargo.insert_one(cargo)
    
    # Создание уведомления
    create_notification(
        current_user.id,
        f"Создан новый груз {cargo_number}. Ожидает обработки.",
        cargo_id
    )
    
    return Cargo(**cargo)

@app.get("/api/cargo/my")
async def get_my_cargo(current_user: User = Depends(get_current_user)):
    cargo_list = list(db.cargo.find({"sender_id": current_user.id}))
    return [Cargo(**cargo) for cargo in cargo_list]

@app.get("/api/cargo/track/{cargo_number}")
async def track_cargo(cargo_number: str):
    cargo = db.cargo.find_one({"cargo_number": cargo_number})
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    return Cargo(**cargo)

@app.get("/api/cargo/all")
async def get_all_cargo(current_user: User = Depends(require_role(UserRole.ADMIN))):
    cargo_list = list(db.cargo.find({}))
    return [Cargo(**cargo) for cargo in cargo_list]

@app.put("/api/cargo/{cargo_id}/status")
async def update_cargo_status(
    cargo_id: str, 
    status: CargoStatus,
    warehouse_location: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    cargo = db.cargo.find_one({"id": cargo_id})
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    update_data = {
        "status": status,
        "updated_at": datetime.utcnow()
    }
    
    if warehouse_location:
        update_data["warehouse_location"] = warehouse_location
    
    db.cargo.update_one({"id": cargo_id}, {"$set": update_data})
    
    # Создание уведомления для отправителя
    status_messages = {
        CargoStatus.ACCEPTED: "принят на склад",
        CargoStatus.IN_TRANSIT: "в пути",
        CargoStatus.ARRIVED_DESTINATION: "прибыл в пункт назначения",
        CargoStatus.COMPLETED: "доставлен получателю"
    }
    
    message = f"Статус груза {cargo['cargo_number']} изменен: {status_messages.get(status, status)}"
    create_notification(cargo["sender_id"], message, cargo_id)
    
    return {"message": "Status updated successfully"}

# Склад
@app.get("/api/warehouse/cargo")
async def get_warehouse_cargo(current_user: User = Depends(require_role(UserRole.WAREHOUSE_OPERATOR))):
    cargo_list = list(db.cargo.find({
        "status": {"$in": [CargoStatus.CREATED, CargoStatus.ACCEPTED, CargoStatus.IN_TRANSIT]}
    }))
    return [Cargo(**cargo) for cargo in cargo_list]

@app.get("/api/warehouse/search")
async def search_cargo(
    query: str,
    current_user: User = Depends(require_role(UserRole.WAREHOUSE_OPERATOR))
):
    # Поиск по номеру груза или имени получателя
    cargo_list = list(db.cargo.find({
        "$or": [
            {"cargo_number": {"$regex": query, "$options": "i"}},
            {"recipient_name": {"$regex": query, "$options": "i"}}
        ]
    }))
    return [Cargo(**cargo) for cargo in cargo_list]

# Администрирование
@app.get("/api/admin/users")
async def get_all_users(current_user: User = Depends(require_role(UserRole.ADMIN))):
    users = list(db.users.find({}, {"password": 0}))
    return [User(**user) for user in users]

@app.put("/api/admin/users/{user_id}/status")
async def toggle_user_status(
    user_id: str,
    is_active: bool,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    result = db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": is_active}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User status updated successfully"}

@app.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = db.users.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

# Уведомления
@app.get("/api/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)):
    notifications = list(db.notifications.find({"user_id": current_user.id}).sort("created_at", -1))
    return [Notification(**notification) for notification in notifications]

@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    result = db.notifications.update_one(
        {"id": notification_id, "user_id": current_user.id},
        {"$set": {"is_read": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)