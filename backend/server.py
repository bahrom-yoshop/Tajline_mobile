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

class OperatorCargoCreate(BaseModel):
    sender_full_name: str = Field(..., min_length=2, max_length=100)
    sender_phone: str = Field(..., min_length=10, max_length=20)
    recipient_full_name: str = Field(..., min_length=2, max_length=100)
    recipient_phone: str = Field(..., min_length=10, max_length=20)
    recipient_address: str = Field(..., min_length=5, max_length=200)
    weight: float = Field(..., gt=0, le=1000)
    declared_value: float = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=500)
    route: RouteType = RouteType.MOSCOW_TO_TAJIKISTAN

class CargoPlacement(BaseModel):
    cargo_id: str
    warehouse_id: str
    block_number: int
    shelf_number: int
    cell_number: int

class CargoWithLocation(BaseModel):
    id: str
    cargo_number: str
    sender_full_name: str
    sender_phone: str
    recipient_full_name: str
    recipient_phone: str
    recipient_address: str
    weight: float
    declared_value: float
    description: str
    route: RouteType
    status: CargoStatus
    payment_status: str = "pending"  # pending, paid, failed
    created_at: datetime
    updated_at: datetime
    created_by: str  # ID оператора, который принял груз
    warehouse_location: Optional[str] = None
    warehouse_id: Optional[str] = None
    block_number: Optional[int] = None
    shelf_number: Optional[int] = None
    cell_number: Optional[int] = None

class PaymentTransaction(BaseModel):
    id: str
    cargo_id: str
    cargo_number: str
    amount_due: float
    amount_paid: float
    payment_date: datetime
    processed_by: str  # ID кассира
    customer_name: str
    customer_phone: str
    transaction_type: str = "cash"  # cash, card, transfer
    notes: Optional[str] = None

class PaymentCreate(BaseModel):
    cargo_number: str
    amount_paid: float
    transaction_type: str = "cash"
    notes: Optional[str] = None

class CargoRequest(BaseModel):
    id: str
    request_number: str
    sender_full_name: str
    sender_phone: str
    recipient_full_name: str
    recipient_phone: str
    recipient_address: str
    pickup_address: str
    cargo_name: str
    weight: float
    declared_value: float
    description: str
    route: RouteType
    status: str = "pending"  # pending, accepted, rejected
    created_at: datetime
    updated_at: datetime
    created_by: str  # ID пользователя
    processed_by: Optional[str] = None  # ID оператора, который обработал

class CargoRequestCreate(BaseModel):
    recipient_full_name: str = Field(..., min_length=2, max_length=100)
    recipient_phone: str = Field(..., min_length=10, max_length=20)
    recipient_address: str = Field(..., min_length=5, max_length=200)
    pickup_address: str = Field(..., min_length=5, max_length=200)
    cargo_name: str = Field(..., min_length=2, max_length=100)
    weight: float = Field(..., gt=0, le=1000)
    declared_value: float = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=500)
    route: RouteType = RouteType.MOSCOW_TO_TAJIKISTAN

class SystemNotification(BaseModel):
    id: str
    title: str
    message: str
    notification_type: str  # cargo_status, payment, request, system
    related_id: Optional[str] = None  # ID груза, заявки и т.д.
    user_id: Optional[str] = None  # Для персональных уведомлений
    is_read: bool = False
    created_at: datetime
    created_by: str

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

def create_system_notification(title: str, message: str, notification_type: str, related_id: str = None, user_id: str = None, created_by: str = None):
    """Создать системное уведомление"""
    notification = {
        "id": str(uuid.uuid4()),
        "title": title,
        "message": message,
        "notification_type": notification_type,
        "related_id": related_id,
        "user_id": user_id,
        "is_read": False,
        "created_at": datetime.utcnow(),
        "created_by": created_by or "system"
    }
    db.system_notifications.insert_one(notification)

def generate_request_number() -> str:
    """Генерировать номер заявки"""
    return f"REQ{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"

def generate_warehouse_structure(warehouse_id: str, blocks_count: int, shelves_per_block: int, cells_per_shelf: int):
    """Generate warehouse structure with blocks, shelves and cells"""
    cells = []
    for block in range(1, blocks_count + 1):
        for shelf in range(1, shelves_per_block + 1):
            for cell in range(1, cells_per_shelf + 1):
                cell_data = {
                    "id": str(uuid.uuid4()),
                    "warehouse_id": warehouse_id,
                    "block_number": block,
                    "shelf_number": shelf,
                    "cell_number": cell,
                    "is_occupied": False,
                    "cargo_id": None,
                    "location_code": f"B{block}-S{shelf}-C{cell}"
                }
                cells.append(cell_data)
    
    # Bulk insert all cells
    if cells:
        db.warehouse_cells.insert_many(cells)
    
    return len(cells)

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

# Управление складами
@app.post("/api/warehouses/create")
async def create_warehouse(
    warehouse_data: WarehouseCreate,
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    warehouse_id = str(uuid.uuid4())
    
    # Рассчитываем общую вместимость
    total_capacity = warehouse_data.blocks_count * warehouse_data.shelves_per_block * warehouse_data.cells_per_shelf
    
    warehouse = {
        "id": warehouse_id,
        "name": warehouse_data.name,
        "location": warehouse_data.location,
        "blocks_count": warehouse_data.blocks_count,
        "shelves_per_block": warehouse_data.shelves_per_block,
        "cells_per_shelf": warehouse_data.cells_per_shelf,
        "total_capacity": total_capacity,
        "created_by": current_user.id,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    # Создаем склад
    db.warehouses.insert_one(warehouse)
    
    # Генерируем структуру склада (блоки, полки, ячейки)
    cells_created = generate_warehouse_structure(
        warehouse_id,
        warehouse_data.blocks_count,
        warehouse_data.shelves_per_block,
        warehouse_data.cells_per_shelf
    )
    
    # Создаем уведомление
    create_notification(
        current_user.id,
        f"Создан новый склад '{warehouse_data.name}' с {cells_created} ячейками",
        None
    )
    
    return Warehouse(**warehouse)

@app.get("/api/warehouses")
async def get_warehouses(current_user: User = Depends(get_current_user)):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if current_user.role == UserRole.ADMIN:
        # Админ видит все склады
        warehouses = list(db.warehouses.find({"is_active": True}))
    else:
        # Оператор видит только свои склады
        warehouses = list(db.warehouses.find({"created_by": current_user.id, "is_active": True}))
    
    return [Warehouse(**warehouse) for warehouse in warehouses]

@app.get("/api/warehouses/{warehouse_id}/structure")
async def get_warehouse_structure(
    warehouse_id: str,
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Проверяем существование склада
    warehouse = db.warehouses.find_one({"id": warehouse_id, "is_active": True})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Получаем все ячейки склада
    cells = list(db.warehouse_cells.find({"warehouse_id": warehouse_id}))
    
    # Группируем ячейки по блокам и полкам
    structure = {}
    for cell in cells:
        block_key = f"block_{cell['block_number']}"
        shelf_key = f"shelf_{cell['shelf_number']}"
        
        if block_key not in structure:
            structure[block_key] = {}
        if shelf_key not in structure[block_key]:
            structure[block_key][shelf_key] = []
        
        structure[block_key][shelf_key].append({
            "cell_id": cell["id"],
            "cell_number": cell["cell_number"],
            "location_code": cell["location_code"],
            "is_occupied": cell["is_occupied"],
            "cargo_id": cell.get("cargo_id")
        })
    
    return {
        "warehouse": Warehouse(**warehouse),
        "structure": structure,
        "total_cells": len(cells),
        "occupied_cells": len([c for c in cells if c["is_occupied"]]),
        "available_cells": len([c for c in cells if not c["is_occupied"]])
    }

@app.put("/api/warehouses/{warehouse_id}/assign-cargo")
async def assign_cargo_to_cell(
    warehouse_id: str,
    cargo_id: str,
    cell_location_code: str,
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Проверяем существование груза
    cargo = db.cargo.find_one({"id": cargo_id})
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Находим ячейку по location_code
    cell = db.warehouse_cells.find_one({
        "warehouse_id": warehouse_id,
        "location_code": cell_location_code,
        "is_occupied": False
    })
    
    if not cell:
        raise HTTPException(status_code=400, detail="Cell not found or already occupied")
    
    # Обновляем ячейку
    db.warehouse_cells.update_one(
        {"id": cell["id"]},
        {"$set": {"is_occupied": True, "cargo_id": cargo_id}}
    )
    
    # Обновляем груз
    db.cargo.update_one(
        {"id": cargo_id},
        {"$set": {"warehouse_location": cell_location_code, "updated_at": datetime.utcnow()}}
    )
    
    # Создаем уведомление для отправителя
    create_notification(
        cargo["sender_id"],
        f"Груз {cargo['cargo_number']} размещен на складе в ячейке {cell_location_code}",
        cargo_id
    )
    
    return {"message": "Cargo assigned to cell successfully", "location": cell_location_code}

@app.delete("/api/warehouses/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    # Проверяем, есть ли грузы в этом складе
    occupied_cells = db.warehouse_cells.find_one({"warehouse_id": warehouse_id, "is_occupied": True})
    if occupied_cells:
        raise HTTPException(status_code=400, detail="Cannot delete warehouse with occupied cells")
    
    # Помечаем склад как неактивный
    result = db.warehouses.update_one(
        {"id": warehouse_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    return {"message": "Warehouse deleted successfully"}

# Управление грузами для операторов
@app.post("/api/operator/cargo/accept")
async def accept_new_cargo(
    cargo_data: OperatorCargoCreate,
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    cargo_id = str(uuid.uuid4())
    cargo_number = generate_cargo_number()
    
    cargo = {
        "id": cargo_id,
        "cargo_number": cargo_number,
        "sender_full_name": cargo_data.sender_full_name,
        "sender_phone": cargo_data.sender_phone,
        "recipient_full_name": cargo_data.recipient_full_name,
        "recipient_phone": cargo_data.recipient_phone,
        "recipient_address": cargo_data.recipient_address,
        "weight": cargo_data.weight,
        "declared_value": cargo_data.declared_value,
        "description": cargo_data.description,
        "route": cargo_data.route,
        "status": CargoStatus.ACCEPTED,
        "payment_status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": current_user.id,
        "warehouse_location": None,
        "warehouse_id": None,
        "block_number": None,
        "shelf_number": None,
        "cell_number": None
    }
    
    db.operator_cargo.insert_one(cargo)
    
    # Создание уведомления
    create_notification(
        current_user.id,
        f"Принят новый груз {cargo_number} от {cargo_data.sender_full_name}",
        cargo_id
    )
    
    return CargoWithLocation(**cargo)

@app.get("/api/operator/cargo/list")
async def get_operator_cargo_list(
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if current_user.role == UserRole.ADMIN:
        # Админ видит все грузы
        cargo_list = list(db.operator_cargo.find({}))
    else:
        # Оператор видит только свои принятые грузы
        cargo_list = list(db.operator_cargo.find({"created_by": current_user.id}))
    
    return [CargoWithLocation(**cargo) for cargo in cargo_list]

@app.post("/api/operator/cargo/place")
async def place_cargo_in_warehouse(
    placement_data: CargoPlacement,
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Проверяем существование груза
    cargo = db.operator_cargo.find_one({"id": placement_data.cargo_id})
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Проверяем существование склада
    warehouse = db.warehouses.find_one({"id": placement_data.warehouse_id, "is_active": True})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Проверяем валидность позиции
    if (placement_data.block_number < 1 or placement_data.block_number > warehouse["blocks_count"] or
        placement_data.shelf_number < 1 or placement_data.shelf_number > warehouse["shelves_per_block"] or
        placement_data.cell_number < 1 or placement_data.cell_number > warehouse["cells_per_shelf"]):
        raise HTTPException(status_code=400, detail="Invalid warehouse position")
    
    location_code = f"B{placement_data.block_number}-S{placement_data.shelf_number}-C{placement_data.cell_number}"
    
    # Проверяем, свободна ли ячейка
    existing_cell = db.warehouse_cells.find_one({
        "warehouse_id": placement_data.warehouse_id,
        "location_code": location_code,
        "is_occupied": True
    })
    
    if existing_cell:
        raise HTTPException(status_code=400, detail="Cell is already occupied")
    
    # Обновляем ячейку
    db.warehouse_cells.update_one(
        {
            "warehouse_id": placement_data.warehouse_id,
            "location_code": location_code
        },
        {"$set": {"is_occupied": True, "cargo_id": placement_data.cargo_id}}
    )
    
    # Обновляем груз
    db.operator_cargo.update_one(
        {"id": placement_data.cargo_id},
        {"$set": {
            "warehouse_location": location_code,
            "warehouse_id": placement_data.warehouse_id,
            "block_number": placement_data.block_number,
            "shelf_number": placement_data.shelf_number,
            "cell_number": placement_data.cell_number,
            "status": CargoStatus.IN_TRANSIT,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Создаем уведомление
    create_notification(
        current_user.id,
        f"Груз {cargo['cargo_number']} размещен в {warehouse['name']}: {location_code}",
        placement_data.cargo_id
    )
    
    return {"message": "Cargo placed successfully", "location": location_code, "warehouse": warehouse["name"]}

@app.get("/api/operator/cargo/available")
async def get_available_cargo_for_placement(
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Получаем грузы без размещения
    query = {"warehouse_location": None, "status": CargoStatus.ACCEPTED}
    if current_user.role != UserRole.ADMIN:
        query["created_by"] = current_user.id
    
    cargo_list = list(db.operator_cargo.find(query))
    return [CargoWithLocation(**cargo) for cargo in cargo_list]

@app.get("/api/operator/cargo/history")
async def get_cargo_history(
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Базовый запрос для доставленных грузов
    query = {"status": CargoStatus.COMPLETED}
    
    # Фильтр по создателю для операторов
    if current_user.role != UserRole.ADMIN:
        query["created_by"] = current_user.id
    
    # Дополнительные фильтры
    if status and status != "all":
        query["payment_status"] = status
    
    if search:
        query["$or"] = [
            {"cargo_number": {"$regex": search, "$options": "i"}},
            {"sender_full_name": {"$regex": search, "$options": "i"}},
            {"recipient_full_name": {"$regex": search, "$options": "i"}}
        ]
    
    cargo_list = list(db.operator_cargo.find(query).sort("updated_at", -1))
    return [CargoWithLocation(**cargo) for cargo in cargo_list]

@app.get("/api/warehouses/{warehouse_id}/available-cells")
async def get_available_cells(
    warehouse_id: str,
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Проверяем существование склада
    warehouse = db.warehouses.find_one({"id": warehouse_id, "is_active": True})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Получаем свободные ячейки
    available_cells = list(db.warehouse_cells.find({
        "warehouse_id": warehouse_id,
        "is_occupied": False
    }, {"_id": 0}).sort([("block_number", 1), ("shelf_number", 1), ("cell_number", 1)]))
    
    # Очищаем данные от MongoDB ObjectId
    clean_warehouse = {
        "id": warehouse["id"],
        "name": warehouse["name"], 
        "location": warehouse["location"],
        "blocks_count": warehouse["blocks_count"],
        "shelves_per_block": warehouse["shelves_per_block"],
        "cells_per_shelf": warehouse["cells_per_shelf"],
        "total_capacity": warehouse["total_capacity"],
        "created_at": warehouse["created_at"],
        "is_active": warehouse["is_active"]
    }
    
    return {
        "warehouse": clean_warehouse,
        "available_cells": available_cells,
        "total_available": len(available_cells)
    }

# Управление кассой и платежами
@app.post("/api/cashier/process-payment")
async def process_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа (администратор или кассир)
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Ищем груз по номеру
    cargo = db.operator_cargo.find_one({"cargo_number": payment_data.cargo_number})
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Проверяем, что груз еще не оплачен
    if cargo.get("payment_status") == "paid":
        raise HTTPException(status_code=400, detail="Cargo already paid")
    
    # Создаем транзакцию
    transaction_id = str(uuid.uuid4())
    transaction = {
        "id": transaction_id,
        "cargo_id": cargo["id"],
        "cargo_number": cargo["cargo_number"],
        "amount_due": cargo["declared_value"],
        "amount_paid": payment_data.amount_paid,
        "payment_date": datetime.utcnow(),
        "processed_by": current_user.id,
        "customer_name": cargo["sender_full_name"],
        "customer_phone": cargo["sender_phone"],
        "transaction_type": payment_data.transaction_type,
        "notes": payment_data.notes
    }
    
    db.payment_transactions.insert_one(transaction)
    
    # Обновляем статус оплаты груза
    db.operator_cargo.update_one(
        {"id": cargo["id"]},
        {"$set": {"payment_status": "paid", "updated_at": datetime.utcnow()}}
    )
    
    # Создаем уведомление
    create_notification(
        current_user.id,
        f"Принята оплата за груз {cargo['cargo_number']} на сумму {payment_data.amount_paid} руб.",
        cargo["id"]
    )
    
    return PaymentTransaction(**transaction)

@app.get("/api/cashier/search-cargo/{cargo_number}")
async def search_cargo_for_payment(
    cargo_number: str,
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Ищем груз по номеру
    cargo = db.operator_cargo.find_one({"cargo_number": cargo_number})
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    return {
        "id": cargo["id"],
        "cargo_number": cargo["cargo_number"],
        "sender_full_name": cargo["sender_full_name"],
        "sender_phone": cargo["sender_phone"],
        "description": cargo["description"],
        "weight": cargo["weight"],
        "declared_value": cargo["declared_value"],
        "payment_status": cargo.get("payment_status", "pending"),
        "created_at": cargo["created_at"]
    }

@app.get("/api/cashier/unpaid-cargo")
async def get_unpaid_cargo(
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Получаем неоплаченные грузы
    unpaid_cargo = list(db.operator_cargo.find({
        "payment_status": {"$ne": "paid"}
    }).sort("created_at", -1))
    
    return [CargoWithLocation(**cargo) for cargo in unpaid_cargo]

@app.get("/api/cashier/payment-history")
async def get_payment_history(
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Получаем историю платежей
    payments = list(db.payment_transactions.find({}).sort("payment_date", -1))
    
    return [PaymentTransaction(**payment) for payment in payments]

# Получение пользователей по ролям
@app.get("/api/admin/users/by-role/{role}")
async def get_users_by_role(
    role: str,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    if role not in ["user", "admin", "warehouse_operator"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    users = list(db.users.find({"role": role}, {"password": 0}))
    return [User(**user) for user in users]

# Получение полной схемы склада
@app.get("/api/warehouses/{warehouse_id}/full-layout")
async def get_warehouse_full_layout(
    warehouse_id: str,
    current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Проверяем существование склада
    warehouse = db.warehouses.find_one({"id": warehouse_id, "is_active": True})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Получаем все ячейки с информацией о грузах
    cells = list(db.warehouse_cells.find({"warehouse_id": warehouse_id}))
    
    # Получаем информацию о грузах в ячейках
    cargo_ids = [cell["cargo_id"] for cell in cells if cell.get("cargo_id")]
    cargo_info = {}
    if cargo_ids:
        cargo_list = list(db.operator_cargo.find({"id": {"$in": cargo_ids}}))
        cargo_info = {cargo["id"]: cargo for cargo in cargo_list}
    
    # Группируем ячейки по блокам и полкам
    layout = {}
    for cell in cells:
        block_key = f"block_{cell['block_number']}"
        shelf_key = f"shelf_{cell['shelf_number']}"
        
        if block_key not in layout:
            layout[block_key] = {"shelves": {}, "block_number": cell['block_number']}
        if shelf_key not in layout[block_key]["shelves"]:
            layout[block_key]["shelves"][shelf_key] = {"cells": [], "shelf_number": cell['shelf_number']}
        
        cell_data = {
            "id": cell["id"],
            "cell_number": cell["cell_number"],
            "location_code": cell["location_code"],
            "is_occupied": cell["is_occupied"],
            "cargo_info": None
        }
        
        if cell.get("cargo_id") and cell["cargo_id"] in cargo_info:
            cargo = cargo_info[cell["cargo_id"]]
            cell_data["cargo_info"] = {
                "cargo_number": cargo["cargo_number"],
                "sender_name": cargo["sender_full_name"],
                "recipient_name": cargo["recipient_full_name"],
                "weight": cargo["weight"],
                "description": cargo["description"]
            }
        
        layout[block_key]["shelves"][shelf_key]["cells"].append(cell_data)
    
    # Сортируем ячейки
    for block in layout.values():
        for shelf in block["shelves"].values():
            shelf["cells"].sort(key=lambda x: x["cell_number"])
    
    # Статистика
    total_cells = len(cells)
    occupied_cells = len([c for c in cells if c["is_occupied"]])
    
    return {
        "warehouse": {
            "id": warehouse["id"],
            "name": warehouse["name"],
            "location": warehouse["location"],
            "blocks_count": warehouse["blocks_count"],
            "shelves_per_block": warehouse["shelves_per_block"],
            "cells_per_shelf": warehouse["cells_per_shelf"]
        },
        "layout": layout,
        "statistics": {
            "total_cells": total_cells,
            "occupied_cells": occupied_cells,
            "available_cells": total_cells - occupied_cells,
            "occupancy_rate": round((occupied_cells / total_cells) * 100, 1) if total_cells > 0 else 0
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)