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
import qrcode
from io import BytesIO
import base64
from PIL import Image
import re
from bson import ObjectId

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

# Utility functions for MongoDB ObjectId serialization
def serialize_mongo_document(document):
    """Converts ObjectId in a MongoDB document to strings recursively."""
    if isinstance(document, list):
        return [serialize_mongo_document(doc) for doc in document]
    
    if isinstance(document, dict):
        serialized = {}
        for key, value in document.items():
            if isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, (dict, list)):
                serialized[key] = serialize_mongo_document(value)
            else:
                serialized[key] = value
        return serialized
    
    return document

def escape_regex_special_chars(text):
    """Escape special regex characters for safe MongoDB regex queries."""
    # Escape all regex special characters
    special_chars = r'\.^$*+?{}[]|()'
    escaped_text = text
    for char in special_chars:
        escaped_text = escaped_text.replace(char, '\\' + char)
    return escaped_text

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
    IN_WAREHOUSE = "in_warehouse"
    COMPLETED = "completed"

class RouteType(str, Enum):
    MOSCOW_TO_TAJIKISTAN = "moscow_to_tajikistan"
    TAJIKISTAN_TO_MOSCOW = "tajikistan_to_moscow"

class TransportStatus(str, Enum):
    EMPTY = "empty"
    FILLED = "filled"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    COMPLETED = "completed"

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
    cargo_name: Optional[str] = Field(None, max_length=100)  # Наименование груза (опционально)
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
    cargo_name: Optional[str]  # Наименование груза (опционально)
    description: str
    declared_value: float
    sender_address: str
    recipient_address: str
    status: CargoStatus
    created_at: datetime
    updated_at: datetime
    warehouse_location: Optional[str] = None
    accepted_by_operator: Optional[str] = None  # ФИО оператора, принявшего груз
    accepted_by_operator_id: Optional[str] = None  # ID оператора
    placed_by_operator: Optional[str] = None  # ФИО оператора, разместившего груз
    placed_by_operator_id: Optional[str] = None  # ID оператора

class TransportCreate(BaseModel):
    driver_name: str = Field(..., min_length=2)
    driver_phone: str = Field(..., min_length=10)
    transport_number: str = Field(..., min_length=3)
    capacity_kg: float = Field(..., gt=0)
    direction: str = Field(..., min_length=3)

class Transport(BaseModel):
    id: str
    transport_number: str
    driver_name: str
    driver_phone: str
    capacity_kg: float
    direction: str
    status: TransportStatus
    current_load_kg: float = 0.0
    cargo_list: List[str] = []  # List of cargo IDs
    created_at: datetime
    updated_at: datetime
    dispatched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TransportCargoPlacement(BaseModel):
    transport_id: str
    cargo_ids: List[str]

class TransportCargoPlacementByNumbers(BaseModel):
    transport_id: str
    cargo_numbers: List[str]  # Номера грузов вместо ID

class OperatorWarehouseBinding(BaseModel):
    id: str
    operator_id: str
    operator_name: str
    operator_phone: str
    warehouse_id: str
    warehouse_name: str
    created_at: datetime
    created_by: str  # Admin who created the binding

class OperatorWarehouseBindingCreate(BaseModel):
    operator_id: str
    warehouse_id: str

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
    cargo_name: Optional[str] = Field(None, max_length=100)  # Наименование груза (опционально)
    declared_value: float = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=500)
    route: RouteType = RouteType.MOSCOW_TO_TAJIKISTAN

class CargoPlacement(BaseModel):
    cargo_id: str
    warehouse_id: str
    block_number: int
    shelf_number: int
    cell_number: int

class CargoPlacementAuto(BaseModel):
    cargo_id: str
    block_number: int
    shelf_number: int  
    cell_number: int
    # warehouse_id will be determined automatically from operator binding

class CargoWithLocation(BaseModel):
    id: str
    cargo_number: str
    sender_full_name: str
    sender_phone: str
    recipient_full_name: str
    recipient_phone: str
    recipient_address: str
    weight: float
    cargo_name: Optional[str]  # Наименование груза (опционально)
    declared_value: float
    description: str
    route: RouteType
    status: CargoStatus
    payment_status: str = "pending"  # pending, paid, failed
    created_at: datetime
    updated_at: datetime
    created_by: str  # ID оператора, который принял груз
    created_by_operator: Optional[str] = None  # ФИО оператора, который принял груз
    target_warehouse_id: Optional[str] = None  # Целевой склад для размещения
    target_warehouse_name: Optional[str] = None  # Название целевого склада
    warehouse_location: Optional[str] = None
    warehouse_id: Optional[str] = None
    block_number: Optional[int] = None
    shelf_number: Optional[int] = None
    cell_number: Optional[int] = None
    placed_by_operator: Optional[str] = None  # ФИО оператора, разместившего груз
    placed_by_operator_id: Optional[str] = None  # ID оператора

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
    notification_type: str
    related_id: Optional[str] = None
    related_data: Optional[dict] = None
    created_by: Optional[str] = None
    created_at: datetime
    is_read: bool = False

# === НОВЫЕ МОДЕЛИ ДЛЯ ЭТАПА 1 ===

# Модели для фото груза
class CargoPhoto(BaseModel):
    id: str
    cargo_id: str
    cargo_number: str
    photo_data: str  # base64 encoded image
    photo_name: str
    photo_size: int  # размер в байтах
    uploaded_by: str  # ID пользователя
    uploaded_by_name: str  # ФИО пользователя
    upload_date: datetime
    photo_type: str = "cargo_photo"  # cargo_photo, damage_photo, packaging_photo
    description: Optional[str] = None

class CargoPhotoUpload(BaseModel):
    cargo_id: str
    photo_data: str  # base64 encoded image  
    photo_name: str
    photo_type: str = "cargo_photo"
    description: Optional[str] = None

# Модели для истории изменений груза
class CargoHistory(BaseModel):
    id: str
    cargo_id: str
    cargo_number: str
    action_type: str  # created, updated, moved, status_changed, placed_on_transport, etc
    field_name: Optional[str] = None  # какое поле изменено
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    description: str  # описание изменения
    changed_by: str  # ID пользователя 
    changed_by_name: str  # ФИО пользователя
    changed_by_role: str  # роль пользователя
    change_date: datetime
    additional_data: Optional[dict] = None

# Модели для комментариев к грузам
class CargoComment(BaseModel):
    id: str
    cargo_id: str
    cargo_number: str
    comment_text: str
    comment_type: str = "general"  # general, issue, note, instruction
    priority: str = "normal"  # low, normal, high, urgent
    is_internal: bool = False  # внутренний комментарий (не видим клиенту)
    author_id: str
    author_name: str
    author_role: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_resolved: bool = False  # для комментариев типа issue

class CargoCommentCreate(BaseModel):
    cargo_id: str
    comment_text: str = Field(..., min_length=1, max_length=1000)
    comment_type: str = "general"
    priority: str = "normal"
    is_internal: bool = False

# Модели для трекинга груза клиентами
class CargoTracking(BaseModel):
    id: str
    cargo_id: str
    cargo_number: str
    tracking_code: str  # уникальный код для клиента
    client_phone: str  # телефон клиента для доступа
    is_active: bool = True
    created_at: datetime
    last_accessed: Optional[datetime] = None
    access_count: int = 0

class CargoTrackingCreate(BaseModel):
    cargo_number: str
    client_phone: str

# Модели для уведомлений клиентам
class ClientNotification(BaseModel):
    id: str
    cargo_id: str
    cargo_number: str
    client_phone: str
    notification_type: str  # sms, email, whatsapp
    message_text: str
    status: str = "pending"  # pending, sent, delivered, failed
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_by: str
    created_at: datetime

class ClientNotificationCreate(BaseModel):
    cargo_id: str
    client_phone: str
    notification_type: str
    message_text: str = Field(..., min_length=1, max_length=500)

# Модели для внутренних сообщений операторов
class InternalMessage(BaseModel):
    id: str
    sender_id: str
    sender_name: str
    recipient_id: str
    recipient_name: str
    message_subject: str
    message_text: str
    priority: str = "normal"  # low, normal, high, urgent
    related_cargo_id: Optional[str] = None
    related_cargo_number: Optional[str] = None
    is_read: bool = False
    sent_at: datetime
    read_at: Optional[datetime] = None

class InternalMessageCreate(BaseModel):
    recipient_id: str
    message_subject: str = Field(..., min_length=1, max_length=200)
    message_text: str = Field(..., min_length=1, max_length=2000)
    priority: str = "normal"
    related_cargo_id: Optional[str] = None

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
    # Генерируем 4-значный номер груза
    # Получаем текущий максимальный номер из обеих коллекций (cargo и operator_cargo)
    try:
        # Ищем последний груз с 4-значным номером в обеих коллекциях
        last_cargo_user = db.cargo.find({
            "cargo_number": {"$regex": "^[0-9]{4}$"}
        }).sort("cargo_number", -1).limit(1)
        
        last_cargo_operator = db.operator_cargo.find({
            "cargo_number": {"$regex": "^[0-9]{4}$"}
        }).sort("cargo_number", -1).limit(1)
        
        last_cargo_user_list = list(last_cargo_user)
        last_cargo_operator_list = list(last_cargo_operator)
        
        # Находим максимальный номер из обеих коллекций
        max_number = 1000  # Начальное значение меньше 1001
        
        if last_cargo_user_list:
            user_number = int(last_cargo_user_list[0]["cargo_number"])
            max_number = max(max_number, user_number)
            
        if last_cargo_operator_list:
            operator_number = int(last_cargo_operator_list[0]["cargo_number"])
            max_number = max(max_number, operator_number)
        
        # Следующий номер
        new_number = max_number + 1 if max_number >= 1001 else 1001
        
        # Проверяем, что номер не превышает 9999
        if new_number > 9999:
            # Если превысили лимит, начинаем с 1001 снова (переиспользуем номера)
            new_number = 1001
        
        # Форматируем как 4-значный номер
        cargo_number = f"{new_number:04d}"
        
        # Проверяем уникальность номера в обеих коллекциях
        while (db.cargo.find_one({"cargo_number": cargo_number}) or 
               db.operator_cargo.find_one({"cargo_number": cargo_number})):
            new_number += 1
            if new_number > 9999:
                new_number = 1001
            cargo_number = f"{new_number:04d}"
        
        return cargo_number
        
    except Exception as e:
        # В случае ошибки, генерируем случайный 4-значный номер
        import random
        return f"{random.randint(1000, 9999):04d}"

def generate_cargo_qr_code(cargo_data: dict) -> str:
    """Генерировать QR код для груза с базовой информацией"""
    try:
        # Формируем данные для QR кода согласно требованиям пользователя
        qr_data = {
            "cargo_number": cargo_data.get("cargo_number", ""),
            "cargo_name": cargo_data.get("cargo_name", cargo_data.get("description", "Груз")),
            "weight": f"{cargo_data.get('weight', 0)} кг",
            "sender": cargo_data.get("sender_full_name", "Не указан"),
            "sender_phone": cargo_data.get("sender_phone", "Не указан"),
            "recipient": cargo_data.get("recipient_full_name", cargo_data.get("recipient_name", "Не указан")),
            "recipient_phone": cargo_data.get("recipient_phone", "Не указан"),
            "city": cargo_data.get("recipient_address", "Не указан")
        }
        
        # Создаем текстовые данные для QR кода
        qr_text = f"""ГРУЗ №{qr_data['cargo_number']}
Наименование: {qr_data['cargo_name']}
Вес: {qr_data['weight']}
Отправитель: {qr_data['sender']}
Тел. отправителя: {qr_data['sender_phone']}
Получатель: {qr_data['recipient']}
Тел. получателя: {qr_data['recipient_phone']}
Город получения: {qr_data['city']}"""
        
        # Генерируем QR код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_text)
        qr.make(fit=True)
        
        # Создаем изображение
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертируем в base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_data}"
        
    except Exception as e:
        print(f"Error generating QR code for cargo: {e}")
        return ""

def generate_warehouse_cell_qr_code(warehouse_data: dict, block: int, shelf: int, cell: int) -> str:
    """Генерировать QR код для ячейки склада"""
    try:
        cell_location = f"{warehouse_data.get('name', 'Склад')}-Б{block}-П{shelf}-Я{cell}"
        
        qr_data = f"""ЯЧЕЙКА СКЛАДА
Местоположение: {cell_location}
Склад: {warehouse_data.get('name', 'Неизвестный склад')}
Адрес склада: {warehouse_data.get('location', 'Не указан')}
Блок: {block}
Полка: {shelf}
Ячейка: {cell}
ID склада: {warehouse_data.get('id', '')}"""
        
        # Генерируем QR код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,
            border=3,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Создаем изображение
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертируем в base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_data}"
        
    except Exception as e:
        print(f"Error generating QR code for warehouse cell: {e}")
        return ""

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

def create_personal_notification(user_id: str, title: str, message: str, notification_type: str, related_id: str = None):
    """Создать персональное уведомление для пользователя"""
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "message": f"{title}: {message}",
        "cargo_id": related_id if notification_type == "cargo" else None,
        "is_read": False,
        "created_at": datetime.utcnow()
    }
    db.notifications.insert_one(notification)

def get_operator_warehouse_ids(operator_id: str) -> list:
    """Получить список ID складов, привязанных к оператору"""
    bindings = list(db.operator_warehouse_bindings.find({"operator_id": operator_id}))
    return [b["warehouse_id"] for b in bindings]

def check_operator_warehouse_binding(operator_id: str, warehouse_id: str) -> bool:
    """Проверить, привязан ли оператор к складу"""
    binding = db.operator_warehouse_bindings.find_one({
        "operator_id": operator_id,
        "warehouse_id": warehouse_id
    })
    return binding is not None

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

def get_operator_warehouses(operator_id: str) -> List[str]:
    """Получить список складов, к которым привязан оператор"""
    bindings = list(db.operator_warehouse_bindings.find({"operator_id": operator_id}))
    return [binding["warehouse_id"] for binding in bindings]

def is_operator_allowed_for_warehouse(operator_id: str, warehouse_id: str) -> bool:
    """Проверить, имеет ли оператор доступ к складу"""
    binding = db.operator_warehouse_bindings.find_one({
        "operator_id": operator_id, 
        "warehouse_id": warehouse_id
    })
    return binding is not None

def get_operator_name_by_id(operator_id: str) -> str:
    """Получить ФИО оператора по ID"""
    user = db.users.find_one({"id": operator_id})
    return user["full_name"] if user else "Неизвестный оператор"

def get_available_cargo_for_transport(operator_id: str = None, user_role: str = None) -> List[dict]:
    """Получить доступные грузы для размещения на транспорт"""
    if user_role == UserRole.ADMIN:
        # Админы видят все грузы со всех складов
        cargo_query = {
            "status": {"$in": ["accepted", "arrived_destination"]},
            "warehouse_location": {"$exists": True, "$ne": None}
        }
    elif user_role == UserRole.WAREHOUSE_OPERATOR and operator_id:
        # Операторы видят только грузы со своих складов
        operator_warehouses = get_operator_warehouses(operator_id)
        if not operator_warehouses:
            return []
        
        cargo_query = {
            "status": {"$in": ["accepted", "arrived_destination"]},
            "warehouse_location": {"$exists": True, "$ne": None},
            "warehouse_id": {"$in": operator_warehouses}
        }
    else:
        return []
    
    # Ищем в обеих коллекциях, исключая MongoDB _id
    user_cargo = list(db.cargo.find(cargo_query, {"_id": 0}))
    operator_cargo = list(db.operator_cargo.find(cargo_query, {"_id": 0}))
    
    return user_cargo + operator_cargo

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

@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# QR Code APIs
@app.get("/api/cargo/{cargo_id}/qr-code")
async def get_cargo_qr_code(
    cargo_id: str,
    current_user: User = Depends(get_current_user)
):
    """Получить QR код для груза"""
    # Ищем груз в обеих коллекциях
    cargo = db.cargo.find_one({"id": cargo_id})
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": cargo_id})
    
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Проверка доступа (пользователь может видеть только свои грузы, админ/оператор - все)
    if current_user.role == UserRole.USER and cargo.get("sender_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    qr_code_data = generate_cargo_qr_code(cargo)
    
    return {
        "cargo_id": cargo_id,
        "cargo_number": cargo.get("cargo_number"),
        "qr_code": qr_code_data
    }

@app.get("/api/warehouse/{warehouse_id}/cell-qr/{block}/{shelf}/{cell}")
async def get_warehouse_cell_qr_code(
    warehouse_id: str,
    block: int,
    shelf: int,
    cell: int,
    current_user: User = Depends(get_current_user)
):
    """Получить QR код для ячейки склада"""
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Найти склад
    warehouse = db.warehouses.find_one({"id": warehouse_id})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Проверить существование ячейки
    if block > warehouse.get("blocks_count", 0) or shelf > warehouse.get("shelves_per_block", 0) or cell > warehouse.get("cells_per_shelf", 0):
        raise HTTPException(status_code=404, detail="Cell not found")
    
    qr_code_data = generate_warehouse_cell_qr_code(warehouse, block, shelf, cell)
    
    return {
        "warehouse_id": warehouse_id,
        "warehouse_name": warehouse.get("name"),
        "location": f"Б{block}-П{shelf}-Я{cell}",
        "qr_code": qr_code_data
    }

@app.get("/api/warehouse/{warehouse_id}/all-cells-qr")
async def get_all_warehouse_cells_qr_codes(
    warehouse_id: str,
    current_user: User = Depends(get_current_user)
):
    """Получить QR коды для всех ячеек склада (для печати)"""
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Найти склад
    warehouse = db.warehouses.find_one({"id": warehouse_id})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    qr_codes = []
    blocks_count = warehouse.get("blocks_count", 1)
    shelves_per_block = warehouse.get("shelves_per_block", 1)
    cells_per_shelf = warehouse.get("cells_per_shelf", 10)
    
    for block in range(1, blocks_count + 1):
        for shelf in range(1, shelves_per_block + 1):
            for cell in range(1, cells_per_shelf + 1):
                qr_code_data = generate_warehouse_cell_qr_code(warehouse, block, shelf, cell)
                qr_codes.append({
                    "block": block,
                    "shelf": shelf,
                    "cell": cell,
                    "location": f"Б{block}-П{shelf}-Я{cell}",
                    "qr_code": qr_code_data
                })
    
    return {
        "warehouse_id": warehouse_id,
        "warehouse_name": warehouse.get("name"),
        "total_cells": len(qr_codes),
        "qr_codes": qr_codes
    }

# QR Code Scanning API
@app.post("/api/qr/scan")
async def scan_qr_code(
    qr_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Обработка отсканированного QR кода"""
    qr_text = qr_data.get("qr_text", "")
    
    if not qr_text:
        raise HTTPException(status_code=400, detail="QR code data is empty")
    
    # Определяем тип QR кода
    if "ГРУЗ №" in qr_text:
        # QR код груза
        try:
            # Извлекаем номер груза
            cargo_number = qr_text.split("ГРУЗ №")[1].split("\n")[0].strip()
            
            # Ищем груз
            cargo = db.cargo.find_one({"cargo_number": cargo_number})
            if not cargo:
                cargo = db.operator_cargo.find_one({"cargo_number": cargo_number})
            
            if not cargo:
                raise HTTPException(status_code=404, detail=f"Cargo {cargo_number} not found")
            
            # Проверка доступа
            if current_user.role == UserRole.USER and cargo.get("sender_id") != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            return {
                "type": "cargo",
                "cargo_id": cargo["id"],
                "cargo_number": cargo["cargo_number"],
                "cargo_name": cargo.get("cargo_name", "Груз"),
                "status": cargo.get("status"),
                "weight": cargo.get("weight"),
                "sender": cargo.get("sender_full_name", "Не указан"),
                "recipient": cargo.get("recipient_full_name", cargo.get("recipient_name", "Не указан")),
                "location": cargo.get("warehouse_location", "Не размещен")
            }
            
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid cargo QR code format")
    
    elif "ЯЧЕЙКА СКЛАДА" in qr_text:
        # QR код ячейки склада
        try:
            # Извлекаем данные ячейки
            lines = qr_text.split("\n")
            location_line = [line for line in lines if "Местоположение:" in line][0]
            location = location_line.split("Местоположение: ")[1].strip()
            
            # Извлекаем warehouse_id
            warehouse_id_line = [line for line in lines if "ID склада:" in line][0]
            warehouse_id = warehouse_id_line.split("ID склада: ")[1].strip()
            
            # Найти склад
            warehouse = db.warehouses.find_one({"id": warehouse_id})
            if not warehouse:
                raise HTTPException(status_code=404, detail="Warehouse not found")
            
            # Проверка доступа
            if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Извлекаем блок, полку, ячейку из локации
            parts = location.split("-")
            if len(parts) >= 3:
                block = int(parts[1][1:])  # Убираем "Б"
                shelf = int(parts[2][1:])  # Убираем "П" 
                cell = int(parts[3][1:])   # Убираем "Я"
                
                # Проверяем, есть ли груз в этой ячейке
                location_code = f"{block}-{shelf}-{cell}"
                warehouse_cell = db.warehouse_cells.find_one({
                    "warehouse_id": warehouse_id,
                    "location_code": location_code
                })
                
                cell_cargo = None
                if warehouse_cell and warehouse_cell.get("is_occupied"):
                    cargo_id = warehouse_cell.get("cargo_id")
                    cell_cargo = db.cargo.find_one({"id": cargo_id})
                    if not cell_cargo:
                        cell_cargo = db.operator_cargo.find_one({"id": cargo_id})
                
                return {
                    "type": "warehouse_cell",
                    "warehouse_id": warehouse_id,
                    "warehouse_name": warehouse.get("name"),
                    "location": location,
                    "block": block,
                    "shelf": shelf,
                    "cell": cell,
                    "is_occupied": warehouse_cell.get("is_occupied", False) if warehouse_cell else False,
                    "cargo": {
                        "cargo_number": cell_cargo.get("cargo_number"),
                        "cargo_name": cell_cargo.get("cargo_name", "Груз"),
                        "weight": cell_cargo.get("weight"),
                        "status": cell_cargo.get("status")
                    } if cell_cargo else None
                }
            
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid warehouse cell QR code format")
    
    else:
        raise HTTPException(status_code=400, detail="Unknown QR code format")

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
        "cargo_name": cargo_data.cargo_name or cargo_data.description[:50],  # Использовать описание как fallback
        "description": cargo_data.description,
        "declared_value": cargo_data.declared_value,
        "sender_address": cargo_data.sender_address,
        "recipient_address": cargo_data.recipient_address,
        "status": CargoStatus.CREATED,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "warehouse_location": None,
        "sender_full_name": current_user.full_name,  # Добавляем для QR кода
        "sender_phone": current_user.phone  # Добавляем для QR кода
    }
    
    # Генерируем QR код для груза
    cargo["qr_code"] = generate_cargo_qr_code(cargo)
    
    db.cargo.insert_one(cargo)
    
    # Создание уведомления
    create_notification(
        current_user.id,
        f"Создан новый груз {cargo_number}. Ожидает обработки.",
        cargo_id
    )
    
    return Cargo(**cargo)

@app.get("/api/operator/my-warehouses")
async def get_operator_warehouses_detailed(
    current_user: User = Depends(get_current_user)
):
    """Расширенный личный кабинет оператора - показать все склады и функции (Функция 2)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if current_user.role == UserRole.ADMIN:
        # Админ видит все склады
        warehouses = list(db.warehouses.find({"is_active": True}))
        is_admin = True
    else:
        # Оператор видит только привязанные склады
        operator_warehouse_ids = get_operator_warehouse_ids(current_user.id)
        
        if not operator_warehouse_ids:
            return {"warehouses": [], "message": "No warehouses assigned to this operator"}
        
        warehouses = list(db.warehouses.find({
            "id": {"$in": operator_warehouse_ids}, 
            "is_active": True
        }))
        is_admin = False
    
    # Получаем расширенную статистику и функции по каждому складу
    warehouse_list = []
    for warehouse in warehouses:
        # Подсчитываем грузы на складе
        cargo_count_user = db.cargo.count_documents({"warehouse_id": warehouse["id"]})
        cargo_count_operator = db.operator_cargo.count_documents({"warehouse_id": warehouse["id"]})
        total_cargo = cargo_count_user + cargo_count_operator
        
        # Подсчитываем занятые ячейки
        occupied_cells = db.warehouse_cells.count_documents({
            "warehouse_id": warehouse["id"], 
            "is_occupied": True
        })
        
        total_cells = warehouse["blocks_count"] * warehouse["shelves_per_block"] * warehouse["cells_per_shelf"]
        
        # Подсчитываем транспорты связанные с этим складом
        related_transports = db.transports.count_documents({
            "$or": [
                {"destination_warehouse_id": warehouse["id"]},
                {"source_warehouse_id": warehouse["id"]},
                {"direction": {"$regex": warehouse["name"], "$options": "i"}}
            ]
        })
        
        # Подсчитываем грузы в разных статусах
        cargo_statuses = {}
        for status in ['accepted', 'placed_in_warehouse', 'on_transport', 'in_transit', 'arrived_destination', 'delivered']:
            count_user = db.cargo.count_documents({"warehouse_id": warehouse["id"], "status": status})
            count_operator = db.operator_cargo.count_documents({"warehouse_id": warehouse["id"], "status": status})
            cargo_statuses[status] = count_user + count_operator
        
        # Получаем список других операторов этого склада (для админов)
        bound_operators = []
        if is_admin:
            bindings = list(db.operator_warehouse_bindings.find({"warehouse_id": warehouse["id"]}))
            for binding in bindings:
                operator = db.users.find_one({"id": binding["operator_id"]}, {"password": 0})
                if operator:
                    bound_operators.append({
                        "id": operator["id"],
                        "full_name": operator["full_name"], 
                        "phone": operator["phone"],
                        "bound_at": binding["created_at"]
                    })
        
        warehouse_info = {
            "id": warehouse["id"],
            "name": warehouse["name"],
            "location": warehouse["location"],
            "blocks_count": warehouse["blocks_count"],
            "shelves_per_block": warehouse["shelves_per_block"],
            "cells_per_shelf": warehouse["cells_per_shelf"],
            "created_at": warehouse.get("created_at"),
            
            # Статистика ячеек
            "cells_info": {
                "total_cells": total_cells,
                "occupied_cells": occupied_cells,
                "free_cells": total_cells - occupied_cells,
                "occupancy_percentage": round((occupied_cells / total_cells) * 100, 1) if total_cells > 0 else 0
            },
            
            # Статистика грузов
            "cargo_info": {
                "total_cargo": total_cargo,
                "user_cargo": cargo_count_user,
                "operator_cargo": cargo_count_operator,
                "by_status": cargo_statuses
            },
            
            # Статистика транспортов
            "transport_info": {
                "related_transports": related_transports
            },
            
            # Доступные функции для этого склада
            "available_functions": {
                "accept_cargo": True,
                "place_cargo": True,
                "move_cargo_between_cells": True,
                "remove_cargo_from_cells": True,
                "view_warehouse_layout": True,
                "search_cargo": True,
                "create_transports": True,
                "manage_arrived_transports": True,
                "generate_qr_codes": True,
                "print_warehouse_reports": True
            },
            
            # Операторы привязанные к складу (только для админов)
            "bound_operators": bound_operators if is_admin else [],
            "operators_count": len(bound_operators) if is_admin else 0,
            
            # Персональная информация
            "is_admin": is_admin,
            "operator_permissions": "full_access" if is_admin else "warehouse_specific"
        }
        
        warehouse_list.append(warehouse_info)
    
    return {
        "warehouses": warehouse_list,
        "total_warehouses": len(warehouse_list),
        "user_role": current_user.role,
        "user_name": current_user.full_name,
        "summary": {
            "total_cargo_across_warehouses": sum(w["cargo_info"]["total_cargo"] for w in warehouse_list),
            "total_occupied_cells": sum(w["cells_info"]["occupied_cells"] for w in warehouse_list),
            "average_occupancy": round(sum(w["cells_info"]["occupancy_percentage"] for w in warehouse_list) / len(warehouse_list), 1) if warehouse_list else 0
        }
    }

@app.get("/api/cargo/my")
async def get_my_cargo(current_user: User = Depends(get_current_user)):
    cargo_list = list(db.cargo.find({"sender_id": current_user.id}))
    # Ensure cargo_name field exists for backward compatibility
    for cargo in cargo_list:
        if 'cargo_name' not in cargo:
            cargo['cargo_name'] = cargo.get('description', 'Груз')[:50] if cargo.get('description') else 'Груз'
    return [Cargo(**cargo) for cargo in cargo_list]

@app.get("/api/cargo/track/{cargo_number}")
async def track_cargo(cargo_number: str):
    cargo = db.cargo.find_one({"cargo_number": cargo_number})
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Ensure cargo_name field exists for backward compatibility
    if 'cargo_name' not in cargo:
        cargo['cargo_name'] = cargo.get('description', 'Груз')[:50] if cargo.get('description') else 'Груз'
    
    return Cargo(**cargo)

@app.get("/api/cargo/all")
async def get_all_cargo(current_user: User = Depends(require_role(UserRole.ADMIN))):
    cargo_list = list(db.cargo.find({}))
    # Ensure cargo_name field exists for backward compatibility
    for cargo in cargo_list:
        if 'cargo_name' not in cargo:
            cargo['cargo_name'] = cargo.get('description', 'Груз')[:50] if cargo.get('description') else 'Груз'
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
    # Ensure cargo_name field exists for backward compatibility
    for cargo in cargo_list:
        if 'cargo_name' not in cargo:
            cargo['cargo_name'] = cargo.get('description', 'Груз')[:50] if cargo.get('description') else 'Груз'
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
    # Ensure cargo_name field exists for backward compatibility
    for cargo in cargo_list:
        if 'cargo_name' not in cargo:
            cargo['cargo_name'] = cargo.get('description', 'Груз')[:50] if cargo.get('description') else 'Груз'
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
    
    # Добавляем информацию о привязанных операторах к каждому складу
    warehouses_with_operators = []
    for warehouse in warehouses:
        # Получаем операторов, привязанных к этому складу
        bindings = list(db.operator_warehouse_bindings.find({"warehouse_id": warehouse["id"]}))
        
        # Получаем информацию об операторах
        bound_operators = []
        for binding in bindings:
            operator = db.users.find_one({"id": binding["operator_id"]}, {"password": 0, "_id": 0})
            if operator:
                bound_operators.append({
                    "id": operator["id"],
                    "full_name": operator["full_name"],
                    "phone": operator["phone"],
                    "bound_at": binding["created_at"]
                })
        
        # Добавляем информацию об операторах к складу
        warehouse_with_operators = {
            **warehouse,
            "bound_operators": bound_operators,
            "operators_count": len(bound_operators)
        }
        warehouses_with_operators.append(warehouse_with_operators)
    
    # Сериализуем все MongoDB ObjectId перед возвратом
    return serialize_mongo_document(warehouses_with_operators)

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
        {"$set": {
            "warehouse_location": cell_location_code, 
            "updated_at": datetime.utcnow(),
            "placed_by_operator": current_user.full_name,
            "placed_by_operator_id": current_user.id
        }}
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
    """Принять новый груз оператором (1.4 - только на привязанные склады)"""
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Для операторов проверяем привязки к складам
    if current_user.role == UserRole.WAREHOUSE_OPERATOR:
        operator_warehouse_ids = get_operator_warehouse_ids(current_user.id)
        if not operator_warehouse_ids:
            raise HTTPException(status_code=403, detail="No warehouses assigned to this operator. Cannot accept cargo.")
        
        # Автоматически выбираем первый привязанный склад как целевой
        target_warehouse_id = operator_warehouse_ids[0]
        warehouse = db.warehouses.find_one({"id": target_warehouse_id})
        if not warehouse:
            raise HTTPException(status_code=404, detail="Target warehouse not found")
    else:
        # Админ может принимать грузы на любой склад - выбираем первый доступный
        all_warehouses = list(db.warehouses.find({"is_active": True}))
        if all_warehouses:
            target_warehouse_id = all_warehouses[0]["id"]
            warehouse = all_warehouses[0]
        else:
            # Если нет активных складов, создаем ошибку вместо None
            raise HTTPException(status_code=400, detail="No active warehouses available for cargo acceptance")
    
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
        "cargo_name": cargo_data.cargo_name or cargo_data.description[:50],  # Использовать описание как fallback
        "declared_value": cargo_data.declared_value,
        "description": cargo_data.description,
        "route": cargo_data.route,
        "status": CargoStatus.ACCEPTED,
        "payment_status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": current_user.id,
        "created_by_operator": current_user.full_name,  # ФИО оператора
        "target_warehouse_id": target_warehouse_id,  # Целевой склад для размещения
        "target_warehouse_name": warehouse.get("name") if warehouse else None,
        "warehouse_location": None,
        "warehouse_id": None,
        "block_number": None,
        "shelf_number": None,
        "cell_number": None,
        "placed_by_operator": None,
        "placed_by_operator_id": None
    }
    
    # Генерируем QR код для груза
    cargo["qr_code"] = generate_cargo_qr_code(cargo)
    
    db.operator_cargo.insert_one(cargo)
    
    # Создание уведомления с информацией о целевом складе
    notification_message = f"Принят новый груз {cargo_number} от {cargo_data.sender_full_name}"
    if warehouse:
        notification_message += f" (целевой склад: {warehouse['name']})"
    
    create_notification(
        current_user.id,
        notification_message,
        cargo_id
    )
    
    return CargoWithLocation(**cargo)

@app.get("/api/operator/cargo/list")
async def get_operator_cargo_list(
    current_user: User = Depends(get_current_user)
):
    """Получить список грузов оператора (только с привязанных складов)"""
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if current_user.role == UserRole.ADMIN:
        # Админ видит все грузы
        cargo_list = list(db.operator_cargo.find({}))
    else:
        # Оператор видит только грузы на привязанных к нему складах
        operator_warehouse_ids = get_operator_warehouse_ids(current_user.id)
        
        if not operator_warehouse_ids:
            # Если оператор не привязан к складам, возвращаем пустой список
            cargo_list = []
        else:
            # Находим грузы на привязанных складах ИЛИ принятые этим оператором
            cargo_list = list(db.operator_cargo.find({
                "$or": [
                    {"warehouse_id": {"$in": operator_warehouse_ids}},  # Грузы на его складах
                    {"created_by": current_user.id}  # Грузы, принятые им лично
                ]
            }))
    
    # Ensure cargo_name field exists for backward compatibility
    for cargo in cargo_list:
        if 'cargo_name' not in cargo:
            cargo['cargo_name'] = cargo.get('description', 'Груз')[:50] if cargo.get('description') else 'Груз'
    
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
            "updated_at": datetime.utcnow(),
            "placed_by_operator": current_user.full_name,
            "placed_by_operator_id": current_user.id
        }}
    )
    
    # Создаем уведомление
    create_notification(
        current_user.id,
        f"Груз {cargo['cargo_number']} размещен в {warehouse['name']}: {location_code}",
        placement_data.cargo_id
    )
    
    return {"message": "Cargo placed successfully", "location": location_code, "warehouse": warehouse["name"]}

@app.post("/api/operator/cargo/place-auto")
async def place_cargo_in_warehouse_auto(
    placement_data: CargoPlacementAuto,
    current_user: User = Depends(get_current_user)
):
    """Размещение груза с автоматическим выбором склада для оператора"""
    # Проверяем права доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Если оператор склада, получаем его привязанные склады
    if current_user.role == UserRole.WAREHOUSE_OPERATOR:
        operator_warehouses = get_operator_warehouses(current_user.id)
        if not operator_warehouses:
            raise HTTPException(status_code=403, detail="No warehouses assigned to this operator")
        
        # Используем первый привязанный склад (можно дать пользователю выбор, если их несколько)
        warehouse_id = operator_warehouses[0]
    else:
        # Для админа нужно указать склад или использовать default
        raise HTTPException(status_code=400, detail="Admin must use regular placement endpoint with warehouse selection")
    
    # Проверяем существование груза
    cargo = db.operator_cargo.find_one({"id": placement_data.cargo_id})
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Проверяем существование склада
    warehouse = db.warehouses.find_one({"id": warehouse_id, "is_active": True})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Assigned warehouse not found")
    
    # Проверяем валидность позиции
    if (placement_data.block_number < 1 or placement_data.block_number > warehouse["blocks_count"] or
        placement_data.shelf_number < 1 or placement_data.shelf_number > warehouse["shelves_per_block"] or
        placement_data.cell_number < 1 or placement_data.cell_number > warehouse["cells_per_shelf"]):
        raise HTTPException(status_code=400, detail="Invalid warehouse position")
    
    location_code = f"B{placement_data.block_number}-S{placement_data.shelf_number}-C{placement_data.cell_number}"
    
    # Проверяем, свободна ли ячейка
    existing_cell = db.warehouse_cells.find_one({
        "warehouse_id": warehouse_id,
        "location_code": location_code,
        "is_occupied": True
    })
    
    if existing_cell:
        raise HTTPException(status_code=400, detail="Cell is already occupied")
    
    # Создаем ячейку если не существует
    db.warehouse_cells.update_one(
        {
            "warehouse_id": warehouse_id,
            "location_code": location_code
        },
        {
            "$set": {
                "warehouse_id": warehouse_id,
                "location_code": location_code,
                "block_number": placement_data.block_number,
                "shelf_number": placement_data.shelf_number,
                "cell_number": placement_data.cell_number,
                "is_occupied": True,
                "cargo_id": placement_data.cargo_id,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    # Обновляем груз
    db.operator_cargo.update_one(
        {"id": placement_data.cargo_id},
        {"$set": {
            "warehouse_location": f"{warehouse['name']} - Блок {placement_data.block_number}, Полка {placement_data.shelf_number}, Ячейка {placement_data.cell_number}",
            "warehouse_id": warehouse_id,
            "block_number": placement_data.block_number,
            "shelf_number": placement_data.shelf_number,
            "cell_number": placement_data.cell_number,
            "status": CargoStatus.IN_TRANSIT,
            "updated_at": datetime.utcnow(),
            "placed_by_operator": current_user.full_name,
            "placed_by_operator_id": current_user.id
        }}
    )
    
    return {"message": "Cargo placed successfully in assigned warehouse", "warehouse_name": warehouse["name"]}

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
    # Ensure cargo_name field exists for backward compatibility
    for cargo in cargo_list:
        if 'cargo_name' not in cargo:
            cargo['cargo_name'] = cargo.get('description', 'Груз')[:50] if cargo.get('description') else 'Груз'
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
    # Ensure cargo_name field exists for backward compatibility
    for cargo in cargo_list:
        if 'cargo_name' not in cargo:
            cargo['cargo_name'] = cargo.get('description', 'Груз')[:50] if cargo.get('description') else 'Груз'
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
    
    # Ensure cargo_name field exists for backward compatibility
    for cargo in unpaid_cargo:
        if 'cargo_name' not in cargo:
            cargo['cargo_name'] = cargo.get('description', 'Груз')[:50] if cargo.get('description') else 'Груз'
    
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
        # Поиск в обеих коллекциях
        cargo_list = list(db.cargo.find({"id": {"$in": cargo_ids}}))
        operator_cargo_list = list(db.operator_cargo.find({"id": {"$in": cargo_ids}}))
        
        # Объединить результаты
        for cargo in cargo_list:
            cargo_info[cargo["id"]] = cargo
        for cargo in operator_cargo_list:
            cargo_info[cargo["id"]] = cargo
    
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
                "sender_name": cargo.get("sender_full_name", "Не указан"),
                "recipient_name": cargo.get("recipient_full_name", cargo.get("recipient_name", "Не указан")),
                "weight": cargo["weight"],
                "description": cargo.get("description", cargo.get("cargo_name", "Груз")),
                "cargo_name": cargo.get("cargo_name", cargo.get("description", "Груз")),
                "status": cargo.get("status", "unknown")
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

# Управление заявками от пользователей
@app.post("/api/user/cargo-request")
async def create_cargo_request(
    request_data: CargoRequestCreate,
    current_user: User = Depends(get_current_user)
):
    # Только обычные пользователи могут создавать заявки
    if current_user.role != UserRole.USER:
        raise HTTPException(status_code=403, detail="Only regular users can create cargo requests")
    
    request_id = str(uuid.uuid4())
    request_number = generate_request_number()
    
    cargo_request = {
        "id": request_id,
        "request_number": request_number,
        "sender_full_name": current_user.full_name,
        "sender_phone": current_user.phone,
        "recipient_full_name": request_data.recipient_full_name,
        "recipient_phone": request_data.recipient_phone,
        "recipient_address": request_data.recipient_address,
        "pickup_address": request_data.pickup_address,
        "cargo_name": request_data.cargo_name,
        "weight": request_data.weight,
        "declared_value": request_data.declared_value,
        "description": request_data.description,
        "route": request_data.route,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": current_user.id,
        "processed_by": None
    }
    
    db.cargo_requests.insert_one(cargo_request)
    
    # Создать системное уведомление для всех операторов и админов
    create_system_notification(
        "Новая заявка на груз",
        f"Пользователь {current_user.full_name} подал заявку на отправку груза №{request_number}",
        "request",
        request_id,
        None,  # Для всех операторов
        current_user.id
    )
    
    # Создать персональное уведомление для пользователя
    create_notification(
        current_user.id,
        f"Ваша заявка №{request_number} принята к рассмотрению",
        request_id
    )
    
    return CargoRequest(**cargo_request)

@app.get("/api/admin/cargo-requests")
async def get_pending_cargo_requests(
    current_user: User = Depends(get_current_user)
):
    # Только админы и операторы могут видеть заявки
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Получаем заявки в статусе pending
    requests = list(db.cargo_requests.find({"status": "pending"}).sort("created_at", -1))
    return [CargoRequest(**request) for request in requests]

@app.get("/api/admin/cargo-requests/all")
async def get_all_cargo_requests(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    # Только админы и операторы могут видеть все заявки
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    query = {}
    if status and status != "all":
        query["status"] = status
    
    requests = list(db.cargo_requests.find(query).sort("created_at", -1))
    return [CargoRequest(**request) for request in requests]

@app.post("/api/admin/cargo-requests/{request_id}/accept")
async def accept_cargo_request(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    # Только админы и операторы могут принимать заявки
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Найти заявку
    request = db.cargo_requests.find_one({"id": request_id, "status": "pending"})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    
    # Создать груз на основе заявки
    cargo_id = str(uuid.uuid4())
    cargo_number = generate_cargo_number()
    
    cargo = {
        "id": cargo_id,
        "cargo_number": cargo_number,
        "sender_full_name": request["sender_full_name"],
        "sender_phone": request["sender_phone"],
        "recipient_full_name": request["recipient_full_name"],
        "recipient_phone": request["recipient_phone"],
        "recipient_address": request["recipient_address"],
        "weight": request["weight"],
        "cargo_name": request.get("cargo_name") or request.get("description", "Груз")[:50],  # Использовать cargo_name или описание
        "declared_value": request["declared_value"],
        "description": request["description"],
        "route": request["route"],
        "status": CargoStatus.ACCEPTED,
        "payment_status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": current_user.id,
        "created_by_operator": current_user.full_name,  # ФИО оператора
        "warehouse_location": None,
        "warehouse_id": None,
        "block_number": None,
        "shelf_number": None,
        "cell_number": None,
        "placed_by_operator": None,
        "placed_by_operator_id": None
    }
    
    db.operator_cargo.insert_one(cargo)
    
    # Обновить статус заявки
    db.cargo_requests.update_one(
        {"id": request_id},
        {"$set": {
            "status": "accepted",
            "processed_by": current_user.id,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Создать уведомления
    create_system_notification(
        "Заявка принята",
        f"Заявка №{request['request_number']} принята оператором {current_user.full_name} и создан груз №{cargo_number}",
        "request",
        request_id,
        None,
        current_user.id
    )
    
    create_notification(
        request["created_by"],
        f"Ваша заявка №{request['request_number']} принята! Создан груз №{cargo_number}",
        cargo_id
    )
    
    return {
        "message": "Request accepted successfully",
        "cargo_number": cargo_number,
        "cargo_id": cargo_id
    }

@app.post("/api/admin/cargo-requests/{request_id}/reject")
async def reject_cargo_request(
    request_id: str,
    reason: str = "",
    current_user: User = Depends(get_current_user)
):
    # Только админы и операторы могут отклонять заявки
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Найти заявку
    request = db.cargo_requests.find_one({"id": request_id, "status": "pending"})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    
    # Обновить статус заявки
    db.cargo_requests.update_one(
        {"id": request_id},
        {"$set": {
            "status": "rejected",
            "processed_by": current_user.id,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Создать уведомления
    create_system_notification(
        "Заявка отклонена",
        f"Заявка №{request['request_number']} отклонена оператором {current_user.full_name}. Причина: {reason}",
        "request",
        request_id,
        None,
        current_user.id
    )
    
    create_notification(
        request["created_by"],
        f"К сожалению, ваша заявка №{request['request_number']} была отклонена. Причина: {reason}",
        request_id
    )
    
    return {"message": "Request rejected successfully"}

# Системные уведомления
@app.get("/api/system-notifications")
async def get_system_notifications(
    notification_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    query = {}
    
    # Операторы и админы видят все уведомления, пользователи - только свои
    if current_user.role == UserRole.USER:
        query["$or"] = [
            {"user_id": current_user.id},
            {"user_id": None, "notification_type": {"$in": ["cargo_status", "payment"]}}
        ]
    
    if notification_type and notification_type != "all":
        query["notification_type"] = notification_type
    
    notifications = list(db.system_notifications.find(query).sort("created_at", -1).limit(100))
    return [SystemNotification(**notification) for notification in notifications]

@app.get("/api/user/my-requests")
async def get_my_cargo_requests(
    current_user: User = Depends(get_current_user)
):
    # Пользователи могут видеть только свои заявки
    requests = list(db.cargo_requests.find({"created_by": current_user.id}).sort("created_at", -1))
    return [CargoRequest(**request) for request in requests]

# === УПРАВЛЕНИЕ ОПЕРАТОРАМИ И СКЛАДАМИ ===

@app.post("/api/admin/operator-warehouse-binding")
async def create_operator_warehouse_binding(
    binding_data: OperatorWarehouseBindingCreate,
    current_user: User = Depends(get_current_user)
):
    # Только админы могут создавать привязки
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create operator-warehouse bindings")
    
    # Проверить, что оператор существует и имеет роль warehouse_operator
    operator = db.users.find_one({"id": binding_data.operator_id})
    if not operator or operator["role"] != UserRole.WAREHOUSE_OPERATOR:
        raise HTTPException(status_code=404, detail="Warehouse operator not found")
    
    # Проверить, что склад существует
    warehouse = db.warehouses.find_one({"id": binding_data.warehouse_id})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Проверить, что привязка не существует
    existing_binding = db.operator_warehouse_bindings.find_one({
        "operator_id": binding_data.operator_id,
        "warehouse_id": binding_data.warehouse_id
    })
    if existing_binding:
        raise HTTPException(status_code=400, detail="Binding already exists")
    
    # Создать привязку
    binding_id = str(uuid.uuid4())
    binding = {
        "id": binding_id,
        "operator_id": binding_data.operator_id,
        "operator_name": operator["full_name"],
        "operator_phone": operator["phone"],
        "warehouse_id": binding_data.warehouse_id,
        "warehouse_name": warehouse["name"],
        "created_at": datetime.utcnow(),
        "created_by": current_user.id
    }
    
    db.operator_warehouse_bindings.insert_one(binding)
    
    # Создать системное уведомление
    create_system_notification(
        "Привязка оператора к складу",
        f"Оператор {operator['full_name']} привязан к складу {warehouse['name']}",
        "operator_binding",
        binding_id,
        None,
        current_user.id
    )
    
    return {"message": "Operator-warehouse binding created successfully", "binding_id": binding_id}

@app.get("/api/admin/operator-warehouse-bindings")
async def get_operator_warehouse_bindings(
    current_user: User = Depends(get_current_user)
):
    # Только админы могут просматривать привязки
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")
    
    bindings = list(db.operator_warehouse_bindings.find({}).sort("created_at", -1))
    return [OperatorWarehouseBinding(**binding) for binding in bindings]

@app.delete("/api/admin/operator-warehouse-binding/{binding_id}")
async def delete_operator_warehouse_binding(
    binding_id: str,
    current_user: User = Depends(get_current_user)
):
    # Только админы могут удалять привязки
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")
    
    binding = db.operator_warehouse_bindings.find_one({"id": binding_id})
    if not binding:
        raise HTTPException(status_code=404, detail="Binding not found")
    
    db.operator_warehouse_bindings.delete_one({"id": binding_id})
    
    # Создать системное уведомление
    create_system_notification(
        "Удалена привязка оператора к складу",
        f"Удалена привязка оператора {binding['operator_name']} к складу {binding['warehouse_name']}",
        "operator_binding",
        binding_id,
        None,
        current_user.id
    )
    
    return {"message": "Operator-warehouse binding deleted successfully"}



@app.get("/api/transport/available-cargo")
async def get_available_cargo_for_transport_endpoint(
    current_user: User = Depends(get_current_user)
):
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    available_cargo = get_available_cargo_for_transport(current_user.id, current_user.role)
    return available_cargo

@app.get("/api/cargo/search")
async def search_cargo_detailed(
    query: str = "",
    search_type: str = "all",  # all, number, sender_name, recipient_name, phone, cargo_name
    current_user: User = Depends(get_current_user)
):
    """Расширенный поиск грузов с детальными карточками и функциями (Функция 4)"""
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not query or len(query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters long")
    
    query = query.strip()
    
    # Построить поисковые критерии
    search_criteria = []
    
    if search_type == "all" or search_type == "number":
        search_criteria.append({"cargo_number": {"$regex": query, "$options": "i"}})
    
    if search_type == "all" or search_type == "sender_name":
        search_criteria.append({"sender_full_name": {"$regex": query, "$options": "i"}})
    
    if search_type == "all" or search_type == "recipient_name":
        search_criteria.append({"recipient_full_name": {"$regex": query, "$options": "i"}})
        search_criteria.append({"recipient_name": {"$regex": query, "$options": "i"}})
    
    if search_type == "all" or search_type == "phone":
        # Экранируем специальные символы regex для безопасного поиска телефонов
        escaped_query = escape_regex_special_chars(query)
        search_criteria.append({"sender_phone": {"$regex": escaped_query, "$options": "i"}})
        search_criteria.append({"recipient_phone": {"$regex": escaped_query, "$options": "i"}})
    
    if search_type == "all" or search_type == "cargo_name":
        search_criteria.append({"cargo_name": {"$regex": query, "$options": "i"}})
        search_criteria.append({"description": {"$regex": query, "$options": "i"}})
    
    if not search_criteria:
        return {"results": [], "total_found": 0, "search_query": query, "search_type": search_type}
    
    # Поиск в коллекции пользовательских грузов
    user_cargo_query = {"$or": search_criteria}
    user_cargo = list(db.cargo.find(user_cargo_query, {"_id": 0}).limit(30))
    
    # Поиск в коллекции операторских грузов  
    operator_cargo = list(db.operator_cargo.find(user_cargo_query, {"_id": 0}).limit(30))
    
    # Объединить результаты
    all_results = user_cargo + operator_cargo
    
    # Сортировать по релевантности (точные совпадения номера сначала)
    if search_type == "number" or query.isdigit():
        all_results.sort(key=lambda x: 0 if x.get("cargo_number", "").lower() == query.lower() else 1)
    
    # Обогащаем каждый результат дополнительными данными и функциями
    enriched_results = []
    for cargo in all_results[:30]:  # Ограничить до 30 результатов
        cargo_id = cargo["id"]
        
        # Получаем информацию о расположении груза
        warehouse_info = None
        location_info = None
        
        if cargo.get("warehouse_id"):
            warehouse = db.warehouses.find_one({"id": cargo["warehouse_id"]}, {"_id": 0})
            if warehouse:
                warehouse_info = {
                    "id": warehouse["id"],
                    "name": warehouse["name"],
                    "location": warehouse["location"]
                }
                
                # Информация о конкретной ячейке
                if cargo.get("block_number") and cargo.get("shelf_number") and cargo.get("cell_number"):
                    location_info = {
                        "block": cargo["block_number"],
                        "shelf": cargo["shelf_number"], 
                        "cell": cargo["cell_number"],
                        "location_code": f"Б{cargo['block_number']}-П{cargo['shelf_number']}-Я{cargo['cell_number']}"
                    }
        
        # Получаем информацию о транспорте (если груз на транспорте)
        transport_info = None
        if cargo.get("transport_id"):
            transport = db.transports.find_one({"id": cargo["transport_id"]}, {"_id": 0})
            if transport:
                transport_info = {
                    "id": transport["id"],
                    "transport_number": transport["transport_number"],
                    "driver_name": transport["driver_name"],
                    "status": transport["status"],
                    "direction": transport["direction"]
                }
        
        # Получаем информацию об операторах
        operator_info = {
            "created_by_operator": cargo.get("created_by_operator"),
            "placed_by_operator": cargo.get("placed_by_operator"),
            "updated_by_operator": cargo.get("updated_by_operator")
        }
        
        # Определяем доступные функции для этого груза
        available_functions = {
            "view_details": True,
            "edit_cargo": True,
            "move_between_cells": cargo.get("status") == "placed_in_warehouse",
            "remove_from_cell": cargo.get("status") == "placed_in_warehouse", 
            "place_on_transport": cargo.get("status") in ["placed_in_warehouse", "accepted"],
            "process_payment": cargo.get("payment_status") == "pending",
            "print_invoice": True,
            "generate_qr_code": True,
            "track_cargo": True,
            "add_notes": True
        }
        
        # Подсчитываем финансовую информацию
        payment_info = {
            "declared_value": cargo.get("declared_value", 0),
            "payment_status": cargo.get("payment_status", "pending"),
            "amount_paid": 0,  # Можно получить из коллекции payments если нужно
            "amount_due": cargo.get("declared_value", 0)
        }
        
        # Создаем обогащенную карточку груза
        enriched_cargo = {
            # Основная информация о грузе
            "id": cargo["id"],
            "cargo_number": cargo["cargo_number"],
            "cargo_name": cargo.get("cargo_name", cargo.get("description", "Груз")[:50]),
            "description": cargo.get("description", ""),
            "weight": cargo.get("weight", 0),
            "status": cargo.get("status", "unknown"),
            "created_at": cargo.get("created_at"),
            "updated_at": cargo.get("updated_at"),
            
            # Информация об отправителе
            "sender": {
                "full_name": cargo.get("sender_full_name", "Не указано"),
                "phone": cargo.get("sender_phone", "Не указано")
            },
            
            # Информация о получателе  
            "recipient": {
                "full_name": cargo.get("recipient_full_name", "Не указано"),
                "phone": cargo.get("recipient_phone", "Не указано"),
                "address": cargo.get("recipient_address", "Не указано")
            },
            
            # Расположение груза
            "location": {
                "warehouse": warehouse_info,
                "cell": location_info,
                "transport": transport_info,
                "status_description": _get_location_description(cargo)
            },
            
            # Информация об операторах
            "operators": operator_info,
            
            # Финансовая информация
            "payment": payment_info,
            
            # Доступные функции
            "available_functions": available_functions,
            
            # Дополнительные поля
            "route": cargo.get("route", "unknown"),
            "qr_code": cargo.get("qr_code", ""),
            "collection_source": "operator_cargo" if cargo.get("created_by_operator") else "cargo"
        }
        
        enriched_results.append(enriched_cargo)
    
    return {
        "results": enriched_results,
        "total_found": len(enriched_results),
        "search_query": query,
        "search_type": search_type,
        "user_role": current_user.role,
        "user_name": current_user.full_name,
        "search_performed_at": datetime.utcnow(),
        "available_search_types": [
            {"value": "all", "label": "Все поля"},
            {"value": "number", "label": "По номеру"},
            {"value": "sender_name", "label": "По ФИО отправителя"},
            {"value": "recipient_name", "label": "По ФИО получателя"},
            {"value": "phone", "label": "По телефону"},
            {"value": "cargo_name", "label": "По названию груза"}
        ]
    }

def _get_location_description(cargo):
    """Получить описание местоположения груза"""
    status = cargo.get("status", "unknown")
    
    if status == "placed_in_warehouse" and cargo.get("warehouse_id"):
        if cargo.get("block_number"):
            return f"На складе в ячейке Б{cargo['block_number']}-П{cargo['shelf_number']}-Я{cargo['cell_number']}"
        else:
            return "На складе (ячейка не указана)"
    elif status == "on_transport" and cargo.get("transport_id"):
        return "На транспорте"
    elif status == "in_transit":
        return "В пути"
    elif status == "accepted":
        return "Принят, ожидает размещения"
    elif status == "delivered":
        return "Доставлен"
    elif status == "arrived_destination":
        return "Прибыл в пункт назначения"
    else:
        return f"Статус: {status}"

# === НОВЫЕ API ЭТАПА 1: ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ГРУЗОВ ===

@app.post("/api/cargo/photo/upload")
async def upload_cargo_photo(
    photo_data: CargoPhotoUpload,
    current_user: User = Depends(get_current_user)
):
    """Загрузить фото груза"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Проверяем существование груза
    cargo = db.cargo.find_one({"id": photo_data.cargo_id})
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": photo_data.cargo_id})
        if not cargo:
            raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Валидация base64 изображения
    try:
        image_data = base64.b64decode(photo_data.photo_data.split(',')[1] if ',' in photo_data.photo_data else photo_data.photo_data)
        image = Image.open(BytesIO(image_data))
        
        # Получаем размер изображения
        photo_size = len(image_data)
        
        # Ограничиваем размер до 5MB
        if photo_size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Photo size too large (max 5MB)")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image data")
    
    # Создаем запись фото
    photo_id = str(uuid.uuid4())
    photo = {
        "id": photo_id,
        "cargo_id": photo_data.cargo_id,
        "cargo_number": cargo["cargo_number"],
        "photo_data": photo_data.photo_data,
        "photo_name": photo_data.photo_name,
        "photo_size": photo_size,
        "uploaded_by": current_user.id,
        "uploaded_by_name": current_user.full_name,
        "upload_date": datetime.utcnow(),
        "photo_type": photo_data.photo_type,
        "description": photo_data.description
    }
    
    db.cargo_photos.insert_one(photo)
    
    # Добавляем в историю груза
    add_cargo_history(
        photo_data.cargo_id,
        cargo["cargo_number"],
        "photo_uploaded",
        None,
        None,
        photo_data.photo_type,
        f"Загружено фото: {photo_data.photo_name}",
        current_user.id,
        current_user.full_name,
        current_user.role,
        {"photo_id": photo_id, "photo_type": photo_data.photo_type}
    )
    
    # Создаем уведомление
    create_notification(
        current_user.id,
        f"Загружено фото для груза {cargo['cargo_number']}",
        photo_data.cargo_id
    )
    
    return {
        "message": "Photo uploaded successfully",
        "photo_id": photo_id,
        "cargo_number": cargo["cargo_number"],
        "photo_size": photo_size
    }

@app.get("/api/cargo/{cargo_id}/photos")
async def get_cargo_photos(
    cargo_id: str,
    current_user: User = Depends(get_current_user)
):
    """Получить все фото груза"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Проверяем существование груза
    cargo = db.cargo.find_one({"id": cargo_id})
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": cargo_id})
        if not cargo:
            raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Получаем фото
    photos = list(db.cargo_photos.find({"cargo_id": cargo_id}, {"_id": 0}).sort("upload_date", -1))
    
    return {
        "cargo_id": cargo_id,
        "cargo_number": cargo["cargo_number"],
        "photos": photos,
        "total_photos": len(photos)
    }

@app.delete("/api/cargo/photo/{photo_id}")
async def delete_cargo_photo(
    photo_id: str,
    current_user: User = Depends(get_current_user)
):
    """Удалить фото груза"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Проверяем существование фото
    photo = db.cargo_photos.find_one({"id": photo_id})
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Удаляем фото
    db.cargo_photos.delete_one({"id": photo_id})
    
    # Добавляем в историю груза
    add_cargo_history(
        photo["cargo_id"],
        photo["cargo_number"],
        "photo_deleted",
        None,
        None,
        None,
        f"Удалено фото: {photo['photo_name']}",
        current_user.id,
        current_user.full_name,
        current_user.role,
        {"photo_id": photo_id, "photo_name": photo["photo_name"]}
    )
    
    return {"message": "Photo deleted successfully"}

@app.get("/api/cargo/{cargo_id}/history")
async def get_cargo_history(
    cargo_id: str,
    current_user: User = Depends(get_current_user)
):
    """Получить историю изменений груза"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Проверяем существование груза
    cargo = db.cargo.find_one({"id": cargo_id})
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": cargo_id})
        if not cargo:
            raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Получаем историю
    history = list(db.cargo_history.find({"cargo_id": cargo_id}, {"_id": 0}).sort("change_date", -1))
    
    return {
        "cargo_id": cargo_id,
        "cargo_number": cargo["cargo_number"],
        "history": history,
        "total_changes": len(history)
    }

@app.post("/api/cargo/comment")
async def add_cargo_comment(
    comment_data: CargoCommentCreate,
    current_user: User = Depends(get_current_user)
):
    """Добавить комментарий к грузу"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Проверяем существование груза
    cargo = db.cargo.find_one({"id": comment_data.cargo_id})
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": comment_data.cargo_id})
        if not cargo:
            raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Создаем комментарий
    comment_id = str(uuid.uuid4())
    comment = {
        "id": comment_id,
        "cargo_id": comment_data.cargo_id,
        "cargo_number": cargo["cargo_number"],
        "comment_text": comment_data.comment_text,
        "comment_type": comment_data.comment_type,
        "priority": comment_data.priority,
        "is_internal": comment_data.is_internal,
        "author_id": current_user.id,
        "author_name": current_user.full_name,
        "author_role": current_user.role,
        "created_at": datetime.utcnow(),
        "is_resolved": False
    }
    
    db.cargo_comments.insert_one(comment)
    
    # Добавляем в историю груза
    add_cargo_history(
        comment_data.cargo_id,
        cargo["cargo_number"],
        "comment_added",
        None,
        None,
        comment_data.comment_type,
        f"Добавлен комментарий ({comment_data.comment_type}): {comment_data.comment_text[:50]}...",
        current_user.id,
        current_user.full_name,
        current_user.role,
        {"comment_id": comment_id, "priority": comment_data.priority}
    )
    
    return {
        "message": "Comment added successfully",
        "comment_id": comment_id,
        "cargo_number": cargo["cargo_number"]
    }

@app.get("/api/cargo/{cargo_id}/comments")
async def get_cargo_comments(
    cargo_id: str,
    include_internal: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Получить комментарии к грузу"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Проверяем существование груза
    cargo = db.cargo.find_one({"id": cargo_id})
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": cargo_id})
        if not cargo:
            raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Фильтруем комментарии
    query = {"cargo_id": cargo_id}
    if not include_internal or current_user.role == UserRole.USER:
        query["is_internal"] = False
    
    comments = list(db.cargo_comments.find(query, {"_id": 0}).sort("created_at", -1))
    
    return {
        "cargo_id": cargo_id,
        "cargo_number": cargo["cargo_number"],
        "comments": comments,
        "total_comments": len(comments)
    }

# Утилитарная функция для добавления записи в историю груза
def add_cargo_history(cargo_id: str, cargo_number: str, action_type: str, 
                     field_name: str = None, old_value: str = None, new_value: str = None,
                     description: str = "", changed_by: str = "", changed_by_name: str = "",
                     changed_by_role: str = "", additional_data: dict = None):
    """Добавить запись в историю изменений груза"""
    history_id = str(uuid.uuid4())
    history_record = {
        "id": history_id,
        "cargo_id": cargo_id,
        "cargo_number": cargo_number,
        "action_type": action_type,
        "field_name": field_name,
        "old_value": old_value,
        "new_value": new_value,
        "description": description,
        "changed_by": changed_by,
        "changed_by_name": changed_by_name,
        "changed_by_role": changed_by_role,
        "change_date": datetime.utcnow(),
        "additional_data": additional_data or {}
    }
    
    db.cargo_history.insert_one(history_record)
    return history_id

# === ТРАНСПОРТ API ===

@app.post("/api/transport/create")
async def create_transport(
    transport: TransportCreate,
    current_user: User = Depends(get_current_user)
):
    # Проверка доступа (только админы и операторы)
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Проверка уникальности номера транспорта
    existing_transport = db.transports.find_one({"transport_number": transport.transport_number})
    if existing_transport:
        raise HTTPException(status_code=400, detail="Transport number already exists")
    
    transport_id = str(uuid.uuid4())
    transport_data = {
        "id": transport_id,
        "transport_number": transport.transport_number,
        "driver_name": transport.driver_name,
        "driver_phone": transport.driver_phone,
        "capacity_kg": transport.capacity_kg,
        "direction": transport.direction,
        "status": TransportStatus.EMPTY,
        "current_load_kg": 0.0,
        "cargo_list": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "dispatched_at": None,
        "completed_at": None
    }
    
    db.transports.insert_one(transport_data)
    
    # Создать системное уведомление
    create_system_notification(
        "Новый транспорт",
        f"Добавлен новый транспорт {transport.transport_number} (водитель: {transport.driver_name})",
        "transport",
        transport_id,
        None,
        current_user.id
    )
    
    return {"message": "Transport created successfully", "transport_id": transport_id}


@app.get("/api/transport/history")
async def get_transport_history(
    current_user: User = Depends(get_current_user)
):
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Получить завершенные и удаленные транспорты
    completed_transports = list(db.transports.find({"status": TransportStatus.COMPLETED}, {"_id": 0}).sort("completed_at", -1))
    deleted_transports = list(db.transport_history.find({}, {"_id": 0}).sort("deleted_at", -1))
    
    history = []
    
    # Добавить завершенные транспорты
    for transport in completed_transports:
        history.append({
            **transport,
            "history_type": "completed"
        })
    
    # Добавить удаленные транспорты
    for transport in deleted_transports:
        history.append({
            **transport,
            "history_type": "deleted"
        })
    
    # Сортировать по дате
    history.sort(key=lambda x: x.get("completed_at") or x.get("deleted_at") or x.get("created_at"), reverse=True)
    
    return history

@app.get("/api/transport/arrived")
async def get_arrived_transports(
    current_user: User = Depends(get_current_user)
):
    """Получить список прибывших транспортов с грузами для размещения"""
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Найти все прибывшие транспорты
    transports = list(db.transports.find({"status": TransportStatus.ARRIVED}))
    
    transport_list = []
    for transport in transports:
        # Получить количество грузов для размещения
        cargo_count = len(transport.get("cargo_list", []))
        
        transport_list.append({
            "id": transport["id"],
            "transport_number": transport["transport_number"],
            "driver_name": transport["driver_name"],
            "driver_phone": transport["driver_phone"],
            "direction": transport["direction"],
            "capacity_kg": transport["capacity_kg"],
            "current_load_kg": transport["current_load_kg"],
            "arrived_at": transport.get("arrived_at"),
            "cargo_count": cargo_count,
            "status": transport["status"]
        })
    
    return transport_list

@app.get("/api/transport/{transport_id}/visualization")
async def get_transport_visualization(
    transport_id: str,
    current_user: User = Depends(get_current_user)
):
    """Получить схему и визуализацию заполнения транспорта"""
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    transport = db.transports.find_one({"id": transport_id})
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    # Получить детальную информацию о грузах
    cargo_details = []
    total_weight = 0
    total_volume_estimate = 0
    
    for cargo_id in transport.get("cargo_list", []):
        cargo = db.cargo.find_one({"id": cargo_id})
        collection_name = "cargo"
        if not cargo:
            cargo = db.operator_cargo.find_one({"id": cargo_id})
            collection_name = "operator_cargo"
        
        if cargo:
            weight = cargo.get("weight", 0)
            total_weight += weight
            # Примерный расчет объема (можно улучшить)
            estimated_volume = weight * 0.001  # м³ (примерно 1кг = 1литр = 0.001м³)
            total_volume_estimate += estimated_volume
            
            cargo_details.append({
                "id": cargo["id"],
                "cargo_number": cargo["cargo_number"],
                "cargo_name": cargo.get("cargo_name", cargo.get("description", "Груз")),
                "weight": weight,
                "estimated_volume": estimated_volume,
                "recipient_name": cargo.get("recipient_full_name", cargo.get("recipient_name", "Не указан")),
                "status": cargo.get("status", "unknown"),
                "collection": collection_name,
                "placement_order": len(cargo_details) + 1
            })
    
    # Расчет заполнения
    capacity_kg = transport.get("capacity_kg", 1000)
    fill_percentage_weight = (total_weight / capacity_kg * 100) if capacity_kg > 0 else 0
    
    # Примерная схема размещения (можно настроить под реальные размеры транспорта)
    transport_length = 12  # метров
    transport_width = 2.5   # метров
    transport_height = 2.8  # метров
    max_volume = transport_length * transport_width * transport_height  # м³
    
    fill_percentage_volume = (total_volume_estimate / max_volume * 100) if max_volume > 0 else 0
    
    # Создаем сетку размещения для визуализации (6x3 = 18 позиций)
    grid_width = 6
    grid_height = 3
    placement_grid = []
    
    for i in range(grid_height):
        row = []
        for j in range(grid_width):
            position_index = i * grid_width + j
            if position_index < len(cargo_details):
                cargo = cargo_details[position_index]
                row.append({
                    "occupied": True,
                    "cargo_id": cargo["id"],
                    "cargo_number": cargo["cargo_number"],
                    "cargo_name": cargo["cargo_name"],
                    "weight": cargo["weight"],
                    "position": f"{i+1}-{j+1}"
                })
            else:
                row.append({
                    "occupied": False,
                    "cargo_id": None,
                    "cargo_number": None,
                    "cargo_name": None,
                    "weight": 0,
                    "position": f"{i+1}-{j+1}"
                })
        placement_grid.append(row)
    
    return {
        "transport": {
            "id": transport["id"],
            "transport_number": transport["transport_number"],
            "driver_name": transport["driver_name"],
            "direction": transport["direction"],
            "capacity_kg": capacity_kg,
            "current_load_kg": total_weight,
            "status": transport["status"],
            "dimensions": {
                "length": transport_length,
                "width": transport_width,
                "height": transport_height,
                "max_volume": max_volume
            }
        },
        "cargo_summary": {
            "total_items": len(cargo_details),
            "total_weight": total_weight,
            "total_volume_estimate": round(total_volume_estimate, 2),
            "fill_percentage_weight": round(fill_percentage_weight, 1),
            "fill_percentage_volume": round(fill_percentage_volume, 1),
            "remaining_capacity_kg": max(0, capacity_kg - total_weight),
            "cargo_list": cargo_details
        },
        "visualization": {
            "grid_width": grid_width,
            "grid_height": grid_height,
            "placement_grid": placement_grid,
            "utilization_status": "overloaded" if fill_percentage_weight > 100 else "full" if fill_percentage_weight > 90 else "partial" if fill_percentage_weight > 50 else "low"
        }
    }

@app.get("/api/transport/list")
async def get_transports_list(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Получить список транспортов с фильтрацией по ролям (1.5)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Базовый запрос с фильтрацией по статусу
    base_query = {}
    if status and status != "all":
        base_query["status"] = status
    
    if current_user.role == UserRole.ADMIN:
        # Админ видит все транспорты
        transports = list(db.transports.find(base_query))
    else:
        # Оператор видит транспорты, связанные с его складами
        operator_warehouse_ids = get_operator_warehouse_ids(current_user.id)
        
        if not operator_warehouse_ids:
            return []
        
        # Получаем названия складов оператора для фильтрации по direction
        operator_warehouses = list(db.warehouses.find({
            "id": {"$in": operator_warehouse_ids}
        }))
        operator_warehouse_names = [w["name"] for w in operator_warehouses]
        
        # Строим сложный запрос для фильтрации транспортов
        query_conditions = [
            {"destination_warehouse_id": {"$in": operator_warehouse_ids}},  # Межскладские к его складам
            {"source_warehouse_id": {"$in": operator_warehouse_ids}},      # Межскладские от его складов
            {"created_by": current_user.id}                                # Созданные им лично
        ]
        
        # Для обычных транспортов проверяем direction (содержит название склада)
        for warehouse_name in operator_warehouse_names:
            query_conditions.append({"direction": {"$regex": warehouse_name, "$options": "i"}})
        
        # Объединяем фильтр по ролям с фильтром по статусу
        final_query = {"$and": [base_query, {"$or": query_conditions}]} if base_query else {"$or": query_conditions}
        transports = list(db.transports.find(final_query))
    
    transport_list = []
    for transport in transports:
        transport_data = {
            "id": transport["id"],
            "transport_number": transport["transport_number"],
            "driver_name": transport["driver_name"],
            "driver_phone": transport["driver_phone"],
            "direction": transport["direction"],
            "capacity_kg": transport["capacity_kg"],
            "current_load_kg": transport["current_load_kg"],
            "status": transport["status"],
            "created_at": transport["created_at"],
            "cargo_list": transport.get("cargo_list", []),
            "source_warehouse_id": transport.get("source_warehouse_id"),
            "destination_warehouse_id": transport.get("destination_warehouse_id"),
            "is_interwarehouse": transport.get("is_interwarehouse", False),
            "dispatched_at": transport.get("dispatched_at"),
            "arrived_at": transport.get("arrived_at")
        }
        transport_list.append(transport_data)
    
    return transport_list

@app.get("/api/warehouses/for-interwarehouse-transport") 
async def get_warehouses_for_interwarehouse_transport(
    current_user: User = Depends(get_current_user)
):
    """Получить список складов для создания межскладских транспортов (Функция 3)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Получаем все активные склады
    all_warehouses = list(db.warehouses.find({"is_active": True}))
    
    # Определяем доступные склады в зависимости от роли
    if current_user.role == UserRole.ADMIN:
        # Админ видит все склады
        accessible_warehouses = all_warehouses
        operator_warehouses = []  # У админа нет привязанных складов
    else:
        # Оператор видит только свои привязанные склады
        operator_warehouse_ids = get_operator_warehouse_ids(current_user.id)
        accessible_warehouses = [w for w in all_warehouses if w["id"] in operator_warehouse_ids]
        operator_warehouses = operator_warehouse_ids
    
    # Автоматически определяем исходный склад для оператора
    auto_source_warehouse = None
    if current_user.role == UserRole.WAREHOUSE_OPERATOR and accessible_warehouses:
        # Для оператора автоматически выбираем первый привязанный склад как исходный
        auto_source_warehouse = accessible_warehouses[0]
    
    # Формируем список складов с дополнительной информацией
    warehouses_info = []
    for warehouse in accessible_warehouses:
        # Подсчитываем грузы готовые к отправке
        ready_cargo_user = db.cargo.count_documents({
            "warehouse_id": warehouse["id"], 
            "status": {"$in": ["placed_in_warehouse", "accepted"]}
        })
        ready_cargo_operator = db.operator_cargo.count_documents({
            "warehouse_id": warehouse["id"], 
            "status": {"$in": ["placed_in_warehouse", "accepted"]}
        })
        total_ready_cargo = ready_cargo_user + ready_cargo_operator
        
        # Получаем операторов, привязанных к складу (для админов)
        bound_operators = []
        if current_user.role == UserRole.ADMIN:
            bindings = list(db.operator_warehouse_bindings.find({"warehouse_id": warehouse["id"]}))
            for binding in bindings:
                operator = db.users.find_one({"id": binding["operator_id"]}, {"password": 0})
                if operator:
                    bound_operators.append({
                        "id": operator["id"],
                        "full_name": operator["full_name"],
                        "phone": operator["phone"]
                    })
        
        warehouse_info = {
            "id": warehouse["id"],
            "name": warehouse["name"],
            "location": warehouse["location"],
            "ready_cargo_count": total_ready_cargo,
            "bound_operators": bound_operators,
            "can_be_source": True,  # Все доступные склады могут быть исходными
            "can_be_destination": True,  # Все доступные склады могут быть целевыми
            "is_operator_warehouse": warehouse["id"] in operator_warehouses if current_user.role == UserRole.WAREHOUSE_OPERATOR else False
        }
        warehouses_info.append(warehouse_info)
    
    return {
        "warehouses": warehouses_info,
        "user_role": current_user.role,
        "user_name": current_user.full_name,
        "auto_source_warehouse": {
            "id": auto_source_warehouse["id"],
            "name": auto_source_warehouse["name"],
            "location": auto_source_warehouse["location"]
        } if auto_source_warehouse else None,
        "total_accessible_warehouses": len(accessible_warehouses),
        "instructions": {
            "for_admin": "Админ может создавать транспорты между любыми складами",
            "for_operator": "Оператор может создавать транспорты только между привязанными складами. Исходный склад выбирается автоматически."
        }
    }

@app.post("/api/transport/create-interwarehouse")
async def create_interwarehouse_transport(
    transport_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Создать улучшенный межскладской транспорт с автоматическим выбором исходного склада (Функция 3)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    source_warehouse_id = transport_data.get("source_warehouse_id")
    destination_warehouse_id = transport_data.get("destination_warehouse_id")
    auto_select_source = transport_data.get("auto_select_source", False)
    
    # Автоматический выбор исходного склада для операторов
    if current_user.role == UserRole.WAREHOUSE_OPERATOR and (auto_select_source or not source_warehouse_id):
        operator_warehouse_ids = get_operator_warehouse_ids(current_user.id)
        if not operator_warehouse_ids:
            raise HTTPException(status_code=403, detail="No warehouses assigned to this operator")
        
        # Автоматически выбираем первый привязанный склад как исходный
        source_warehouse_id = operator_warehouse_ids[0]
        
    if not source_warehouse_id or not destination_warehouse_id:
        raise HTTPException(status_code=400, detail="Source and destination warehouses required")
    
    if source_warehouse_id == destination_warehouse_id:
        raise HTTPException(status_code=400, detail="Source and destination warehouses must be different")
    
    # Для операторов проверяем доступ к складам
    if current_user.role == UserRole.WAREHOUSE_OPERATOR:
        operator_warehouse_ids = get_operator_warehouse_ids(current_user.id)
        
        # Оператор должен иметь доступ к ОБОИМ складам (исходному И целевому)
        if source_warehouse_id not in operator_warehouse_ids:
            raise HTTPException(status_code=403, detail="No access to source warehouse")
        
        if destination_warehouse_id not in operator_warehouse_ids:
            raise HTTPException(status_code=403, detail="No access to destination warehouse")
    
    # Проверяем существование складов
    source_warehouse = db.warehouses.find_one({"id": source_warehouse_id})
    destination_warehouse = db.warehouses.find_one({"id": destination_warehouse_id})
    
    if not source_warehouse or not destination_warehouse:
        raise HTTPException(status_code=404, detail="Source or destination warehouse not found")
    
    # Подсчитываем доступные грузы на исходном складе
    available_cargo_user = db.cargo.count_documents({
        "warehouse_id": source_warehouse_id, 
        "status": {"$in": ["placed_in_warehouse", "accepted"]}
    })
    available_cargo_operator = db.operator_cargo.count_documents({
        "warehouse_id": source_warehouse_id, 
        "status": {"$in": ["placed_in_warehouse", "accepted"]}
    })
    total_available_cargo = available_cargo_user + available_cargo_operator
    
    # Создаем транспорт
    transport_id = str(uuid.uuid4())
    transport_number = f"IW-{transport_id[-8:].upper()}"  # Межскладской префикс
    
    direction = f"{source_warehouse['name']} → {destination_warehouse['name']}"
    
    transport = {
        "id": transport_id,
        "transport_number": transport_number,
        "driver_name": transport_data.get("driver_name", ""),
        "driver_phone": transport_data.get("driver_phone", ""),
        "direction": direction,
        "capacity_kg": transport_data.get("capacity_kg", 1000),
        "current_load_kg": 0,
        "status": TransportStatus.EMPTY,
        "cargo_list": [],
        "is_interwarehouse": True,
        "source_warehouse_id": source_warehouse_id,
        "source_warehouse_name": source_warehouse["name"],
        "destination_warehouse_id": destination_warehouse_id,
        "destination_warehouse_name": destination_warehouse["name"],
        "created_at": datetime.utcnow(),
        "created_by": current_user.id,
        "created_by_name": current_user.full_name,
        "auto_selected_source": auto_select_source or (current_user.role == UserRole.WAREHOUSE_OPERATOR and not transport_data.get("source_warehouse_id")),
        "available_cargo_at_source": total_available_cargo
    }
    
    db.transports.insert_one(transport)
    
    # Создать уведомление
    notification_message = f"Создан межскладской транспорт {transport_number}: {direction}"
    if transport["auto_selected_source"]:
        notification_message += f" (исходный склад выбран автоматически)"
    
    create_system_notification(
        "Новый межскладской транспорт",
        notification_message,
        "transport",
        transport_id,
        None,
        current_user.id
    )
    
    return {
        "message": "Interwarehouse transport created successfully", 
        "transport_id": transport_id,
        "transport_number": transport_number,
        "source_warehouse": {
            "id": source_warehouse_id,
            "name": source_warehouse["name"]
        },
        "destination_warehouse": {
            "id": destination_warehouse_id, 
            "name": destination_warehouse["name"]
        },
        "auto_selected_source": transport["auto_selected_source"],
        "available_cargo_at_source": total_available_cargo,
        "created_by": current_user.full_name
    }

@app.get("/api/transport/{transport_id}")
async def get_transport(
    transport_id: str,
    current_user: User = Depends(get_current_user)
):
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    transport = db.transports.find_one({"id": transport_id})
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    return Transport(**transport)

@app.get("/api/transport/{transport_id}/cargo-list")
async def get_transport_cargo(
    transport_id: str,
    current_user: User = Depends(get_current_user)
):
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    transport = db.transports.find_one({"id": transport_id})
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    # Получить детали грузов
    cargo_details = []
    for cargo_id in transport.get("cargo_list", []):
        cargo = db.cargo.find_one({"id": cargo_id})
        if not cargo:
            cargo = db.operator_cargo.find_one({"id": cargo_id})
        
        if cargo:
            cargo_details.append({
                "id": cargo["id"],
                "cargo_number": cargo["cargo_number"],
                "cargo_name": cargo.get("cargo_name", cargo.get("description", "Груз")),
                "description": cargo.get("description", ""),
                "weight": cargo["weight"],
                "declared_value": cargo["declared_value"],
                "recipient_name": cargo.get("recipient_name") or cargo.get("recipient_full_name", "Не указан"),
                "sender_full_name": cargo.get("sender_full_name", "Не указан"),
                "sender_phone": cargo.get("sender_phone", "Не указан"),
                "recipient_phone": cargo.get("recipient_phone", "Не указан"),
                "status": cargo.get("status", "unknown")
            })
    
    return {
        "transport": Transport(**transport),
        "cargo_list": cargo_details,
        "total_weight": sum(c["weight"] for c in cargo_details),
        "cargo_count": len(cargo_details)
    }

@app.post("/api/transport/{transport_id}/place-cargo")
async def place_cargo_on_transport(
    transport_id: str,
    placement: TransportCargoPlacementByNumbers,
    current_user: User = Depends(get_current_user)
):
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    transport = db.transports.find_one({"id": transport_id})
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    if transport["status"] not in [TransportStatus.EMPTY, TransportStatus.FILLED]:
        raise HTTPException(status_code=400, detail="Cannot place cargo on transport in current status")
    
    # Найти грузы по номерам из всех коллекций и складов
    total_weight = 0
    cargo_details = []
    found_cargo_ids = []
    
    for cargo_number in placement.cargo_numbers:
        cargo_number = cargo_number.strip()
        if not cargo_number:
            continue
            
        # Искать в коллекции пользовательских грузов
        cargo = db.cargo.find_one({"cargo_number": cargo_number})
        if not cargo:
            # Искать в коллекции операторских грузов
            cargo = db.operator_cargo.find_one({"cargo_number": cargo_number})
        
        if not cargo:
            raise HTTPException(status_code=404, detail=f"Cargo {cargo_number} not found")
        
        # Проверить права доступа оператора к складу (если это не админ)
        if current_user.role == UserRole.WAREHOUSE_OPERATOR:
            if cargo.get("warehouse_id"):
                if not is_operator_allowed_for_warehouse(current_user.id, cargo["warehouse_id"]):
                    raise HTTPException(status_code=403, detail=f"Access denied to cargo {cargo_number} - not your warehouse")
        
        # Проверить, что груз на складе и доступен для загрузки
        if cargo["status"] not in ["accepted", "arrived_destination", "in_transit"]:
            raise HTTPException(status_code=400, detail=f"Cargo {cargo_number} is not available for loading (status: {cargo['status']})")
        
        if not cargo.get("warehouse_location"):
            raise HTTPException(status_code=400, detail=f"Cargo {cargo_number} is not in warehouse")
        
        total_weight += cargo["weight"]
        cargo_details.append(cargo)
        found_cargo_ids.append(cargo["id"])
    
    if not cargo_details:
        raise HTTPException(status_code=400, detail="No valid cargo numbers provided")
    
    # Проверить, что груз помещается в транспорт
    current_load = transport.get("current_load_kg", 0)
    if current_load + total_weight > transport["capacity_kg"]:
        raise HTTPException(status_code=400, detail=f"Transport capacity exceeded: current {current_load}kg + new {total_weight}kg > capacity {transport['capacity_kg']}kg")
    
    # Обновить транспорт
    new_cargo_list = list(set(transport.get("cargo_list", []) + found_cargo_ids))
    new_load = current_load + total_weight
    new_status = TransportStatus.FILLED if new_load >= transport["capacity_kg"] * 0.9 else transport["status"]
    
    db.transports.update_one(
        {"id": transport_id},
        {"$set": {
            "cargo_list": new_cargo_list,
            "current_load_kg": new_load,
            "status": new_status,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Обновить статус грузов и освободить ячейки склада
    for cargo in cargo_details:
        # Определить, в какой коллекции находится груз
        collection = db.cargo if db.cargo.find_one({"id": cargo["id"]}) else db.operator_cargo
        
        # Обновить статус груза
        collection.update_one(
            {"id": cargo["id"]},
            {"$set": {
                "status": "in_transit",
                "updated_at": datetime.utcnow(),
                "transport_id": transport_id
            }}
        )
        
        # Освободить ячейку склада
        if cargo.get("warehouse_location") and cargo.get("warehouse_id"):
            # Найти и освободить ячейку
            warehouse_id = cargo["warehouse_id"]
            block_num = cargo.get("block_number")
            shelf_num = cargo.get("shelf_number") 
            cell_num = cargo.get("cell_number")
            
            if block_num and shelf_num and cell_num:
                location_code = f"B{block_num}-S{shelf_num}-C{cell_num}"
                
                # Освободить ячейку
                db.warehouse_cells.update_one(
                    {
                        "warehouse_id": warehouse_id,
                        "location_code": location_code,
                        "cargo_id": cargo["id"]
                    },
                    {"$set": {
                        "is_occupied": False,
                        "updated_at": datetime.utcnow()
                    }, "$unset": {"cargo_id": ""}}
                )
                
                print(f"Freed warehouse cell {location_code} in warehouse {warehouse_id} for cargo {cargo['cargo_number']}")
        
        # Очистить местоположение груза 
        collection.update_one(
            {"id": cargo["id"]},
            {"$unset": {
                "warehouse_location": "",
                "warehouse_id": "",
                "block_number": "",
                "shelf_number": "",
                "cell_number": ""
            }}
        )
        
        # Создать уведомление пользователю (если есть sender_id)
        sender_id = cargo.get("sender_id") or cargo.get("created_by")
        if sender_id:
            create_notification(
                sender_id,
                f"Ваш груз {cargo['cargo_number']} загружен в транспорт {transport['transport_number']} и готов к отправке",
                cargo["id"]
            )
    
    return {
        "message": f"Successfully placed {len(found_cargo_ids)} cargo items on transport",
        "cargo_count": len(found_cargo_ids),
        "total_weight": total_weight,
        "cargo_numbers": [cargo["cargo_number"] for cargo in cargo_details]
    }

@app.post("/api/transport/{transport_id}/dispatch")
async def dispatch_transport(
    transport_id: str,
    current_user: User = Depends(get_current_user)
):
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    transport = db.transports.find_one({"id": transport_id})
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    # Проверяем, что транспорт не в пути уже
    if transport["status"] == TransportStatus.IN_TRANSIT:
        raise HTTPException(status_code=400, detail="Transport is already in transit")
    
    # Разрешаем отправку транспорта с любым объемом груза
    # Убираем проверку на обязательное заполнение до 90%
    
    # Обновить статус транспорта
    db.transports.update_one(
        {"id": transport_id},
        {"$set": {
            "status": TransportStatus.IN_TRANSIT,
            "dispatched_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Обновить статус всех грузов и отправить уведомления
    for cargo_id in transport.get("cargo_list", []):
        cargo = db.cargo.find_one({"id": cargo_id})
        if cargo:
            # Обновить статус груза
            db.cargo.update_one(
                {"id": cargo_id},
                {"$set": {
                    "status": "in_transit",
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Создать уведомление пользователю
            create_notification(
                cargo["sender_id"],
                f"Ваш груз {cargo['cargo_number']} отправлен в место назначения на транспорте {transport['transport_number']}",
                cargo_id
            )
    
    # Создать системное уведомление
    create_system_notification(
        "Транспорт отправлен",
        f"Транспорт {transport['transport_number']} отправлен в направлении {transport['direction']} с {len(transport.get('cargo_list', []))} грузами",
        "transport",
        transport_id,
        None,
        current_user.id
    )
    
    return {"message": "Transport dispatched successfully"}

@app.post("/api/transport/{transport_id}/arrive")
async def mark_transport_arrived(
    transport_id: str,
    current_user: User = Depends(get_current_user)
):
    """Отметить транспорт как прибывший"""
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    transport = db.transports.find_one({"id": transport_id})
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    if transport["status"] != TransportStatus.IN_TRANSIT:
        raise HTTPException(status_code=400, detail="Transport must be in transit to mark as arrived")
    
    # Обновить статус транспорта
    db.transports.update_one(
        {"id": transport_id},
        {"$set": {
            "status": TransportStatus.ARRIVED,
            "arrived_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Обновить статус всех грузов на arrived_destination
    for cargo_id in transport.get("cargo_list", []):
        # Поиск в обеих коллекциях
        cargo = db.cargo.find_one({"id": cargo_id})
        collection_name = "cargo"
        if not cargo:
            cargo = db.operator_cargo.find_one({"id": cargo_id})
            collection_name = "operator_cargo"
        
        if cargo:
            # Обновить статус груза
            db[collection_name].update_one(
                {"id": cargo_id},
                {"$set": {
                    "status": CargoStatus.ARRIVED_DESTINATION,
                    "arrived_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Создать уведомление пользователю
            if collection_name == "cargo":
                create_personal_notification(
                    cargo["sender_id"], 
                    "Груз прибыл", 
                    f"Ваш груз №{cargo['cargo_number']} прибыл в место назначения",
                    "cargo",
                    cargo_id
                )
    
    # Создать системное уведомление
    create_system_notification(
        "Транспорт прибыл",
        f"Транспорт {transport['transport_number']} прибыл в место назначения с {len(transport.get('cargo_list', []))} грузами",
        "transport",
        transport_id,
        None,
        current_user.id
    )
    
    return {"message": "Transport marked as arrived successfully"}

@app.get("/api/transport/{transport_id}/arrived-cargo")
async def get_arrived_transport_cargo(
    transport_id: str,
    current_user: User = Depends(get_current_user)
):
    """Получить грузы из прибывшего транспорта для размещения на складе"""
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    transport = db.transports.find_one({"id": transport_id})
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    if transport["status"] != TransportStatus.ARRIVED:
        raise HTTPException(status_code=400, detail="Transport must be arrived to access cargo for placement")
    
    # Получить детали грузов для размещения
    cargo_details = []
    for cargo_id in transport.get("cargo_list", []):
        cargo = db.cargo.find_one({"id": cargo_id})
        collection_name = "cargo"
        if not cargo:
            cargo = db.operator_cargo.find_one({"id": cargo_id})
            collection_name = "operator_cargo"
        
        if cargo:
            cargo_details.append({
                "id": cargo["id"],
                "cargo_number": cargo["cargo_number"],
                "cargo_name": cargo.get("cargo_name", cargo.get("description", "Груз")),
                "description": cargo.get("description", ""),
                "weight": cargo["weight"],
                "declared_value": cargo["declared_value"],
                "sender_full_name": cargo.get("sender_full_name", "Не указан"),
                "sender_phone": cargo.get("sender_phone", "Не указан"),
                "recipient_full_name": cargo.get("recipient_full_name", cargo.get("recipient_name", "Не указан")),
                "recipient_phone": cargo.get("recipient_phone", "Не указан"),
                "recipient_address": cargo.get("recipient_address", "Не указан"),
                "status": cargo.get("status", "unknown"),
                "route": cargo.get("route", "unknown"),
                "collection": collection_name,
                "can_be_placed": cargo.get("status") == CargoStatus.ARRIVED_DESTINATION
            })
    
    return {
        "transport": {
            "id": transport["id"],
            "transport_number": transport["transport_number"],
            "driver_name": transport["driver_name"],
            "direction": transport["direction"],
            "arrived_at": transport.get("arrived_at"),
            "status": transport["status"]
        },
        "cargo_list": cargo_details,
        "total_weight": sum(c["weight"] for c in cargo_details),
        "cargo_count": len(cargo_details),
        "placeable_cargo_count": len([c for c in cargo_details if c["can_be_placed"]])
    }

@app.post("/api/transport/{transport_id}/place-cargo-to-warehouse")
async def place_cargo_from_transport_to_warehouse(
    transport_id: str,
    placement: dict,
    current_user: User = Depends(get_current_user)
):
    """Разместить груз из прибывшего транспорта на склад"""
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    transport = db.transports.find_one({"id": transport_id})
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    if transport["status"] != TransportStatus.ARRIVED:
        raise HTTPException(status_code=400, detail="Transport must be arrived to place cargo")
    
    cargo_id = placement.get("cargo_id")
    warehouse_id = placement.get("warehouse_id")
    block_number = placement.get("block_number")
    shelf_number = placement.get("shelf_number")
    cell_number = placement.get("cell_number")
    
    if not all([cargo_id, warehouse_id, block_number, shelf_number, cell_number]):
        raise HTTPException(status_code=400, detail="Missing required placement data")
    
    # Проверить, что груз на этом транспорте
    if cargo_id not in transport.get("cargo_list", []):
        raise HTTPException(status_code=400, detail="Cargo is not on this transport")
    
    # Найти груз в обеих коллекциях
    cargo = db.cargo.find_one({"id": cargo_id})
    collection_name = "cargo"
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": cargo_id})
        collection_name = "operator_cargo"
    
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    if cargo.get("status") != CargoStatus.ARRIVED_DESTINATION:
        raise HTTPException(status_code=400, detail="Cargo must be in arrived_destination status to place")
    
    # Найти склад
    warehouse = db.warehouses.find_one({"id": warehouse_id})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Проверить валидность ячейки
    if (block_number > warehouse.get("blocks_count", 0) or 
        shelf_number > warehouse.get("shelves_per_block", 0) or 
        cell_number > warehouse.get("cells_per_shelf", 0)):
        raise HTTPException(status_code=400, detail="Invalid cell coordinates")
    
    # Проверить доступность ячейки
    location_code = f"{block_number}-{shelf_number}-{cell_number}"
    existing_cell = db.warehouse_cells.find_one({
        "warehouse_id": warehouse_id,
        "location_code": location_code
    })
    
    if existing_cell and existing_cell.get("is_occupied", False):
        raise HTTPException(status_code=400, detail=f"Cell {location_code} is already occupied")
    
    # Проверить права оператора на склад (если не админ)
    if current_user.role == UserRole.WAREHOUSE_OPERATOR:
        if not check_operator_warehouse_binding(current_user.id, warehouse_id):
            raise HTTPException(status_code=403, detail="Operator not bound to this warehouse")
    
    # Разместить груз в ячейке
    if existing_cell:
        # Обновить существующую ячейку
        db.warehouse_cells.update_one(
            {"_id": existing_cell["_id"]},
            {"$set": {
                "is_occupied": True,
                "cargo_id": cargo_id,
                "placed_at": datetime.utcnow(),
                "placed_by": current_user.id,
                "updated_at": datetime.utcnow()
            }}
        )
    else:
        # Создать новую ячейку
        db.warehouse_cells.insert_one({
            "warehouse_id": warehouse_id,
            "location_code": location_code,
            "block_number": block_number,
            "shelf_number": shelf_number,
            "cell_number": cell_number,
            "is_occupied": True,
            "cargo_id": cargo_id,
            "placed_at": datetime.utcnow(),
            "placed_by": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
    
    # Обновить груз
    collection = db[collection_name]
    collection.update_one(
        {"id": cargo_id},
        {"$set": {
            "status": CargoStatus.IN_WAREHOUSE,
            "warehouse_id": warehouse_id,
            "warehouse_location": warehouse.get("name"),
            "block_number": block_number,
            "shelf_number": shelf_number,
            "cell_number": cell_number,
            "placed_by_operator": current_user.full_name,
            "placed_by_operator_id": current_user.id,
            "placed_at": datetime.utcnow(),
            "transport_id": None,  # Убираем связь с транспортом
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Удалить груз из списка транспорта
    updated_cargo_list = [cid for cid in transport.get("cargo_list", []) if cid != cargo_id]
    new_load = max(0, transport.get("current_load_kg", 0) - cargo.get("weight", 0))
    
    # Обновить транспорт
    new_status = TransportStatus.COMPLETED if len(updated_cargo_list) == 0 else TransportStatus.ARRIVED
    db.transports.update_one(
        {"id": transport_id},
        {"$set": {
            "cargo_list": updated_cargo_list,
            "current_load_kg": new_load,
            "status": new_status,
            "completed_at": datetime.utcnow() if new_status == TransportStatus.COMPLETED else None,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Создать уведомления
    if collection_name == "cargo":
        create_personal_notification(
            cargo["sender_id"], 
            "Груз размещен на складе", 
            f"Ваш груз №{cargo['cargo_number']} размещен на складе {warehouse.get('name')} в ячейке Б{block_number}-П{shelf_number}-Я{cell_number}",
            "cargo",
            cargo_id
        )
    
    create_system_notification(
        "Груз размещен из транспорта",
        f"Груз №{cargo['cargo_number']} размещен из транспорта {transport['transport_number']} на склад {warehouse.get('name')} в ячейку {location_code}",
        "cargo",
        cargo_id,
        None,
        current_user.id
    )
    
    return {
        "message": f"Cargo {cargo['cargo_number']} successfully placed in warehouse",
        "cargo_number": cargo["cargo_number"],
        "warehouse_name": warehouse.get("name"),
        "location": f"Б{block_number}-П{shelf_number}-Я{cell_number}",
        "transport_status": new_status,
        "remaining_cargo": len(updated_cargo_list)
    }

@app.post("/api/transport/{transport_id}/place-cargo-by-number")
async def place_cargo_from_transport_by_number(
    transport_id: str,
    placement_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Разместить груз из транспорта по номеру/QR коду с автоматическим выбором склада, но ручным выбором ячейки"""
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    transport = db.transports.find_one({"id": transport_id})
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    if transport["status"] != TransportStatus.ARRIVED:
        raise HTTPException(status_code=400, detail="Transport must be arrived to place cargo")
    
    cargo_number = placement_data.get("cargo_number", "").strip()
    qr_data = placement_data.get("qr_data", "").strip()
    
    # Получение данных ячейки: может быть QR ячейки или координаты ячейки
    cell_qr_data = placement_data.get("cell_qr_data", "").strip()
    block_number = placement_data.get("block_number")
    shelf_number = placement_data.get("shelf_number")
    cell_number = placement_data.get("cell_number")
    
    # Определить номер груза из QR кода или использовать прямой номер
    if qr_data and "ГРУЗ №" in qr_data:
        try:
            cargo_number = qr_data.split("ГРУЗ №")[1].split("\n")[0].strip()
        except:
            raise HTTPException(status_code=400, detail="Invalid cargo QR code format")
    
    if not cargo_number:
        raise HTTPException(status_code=400, detail="Cargo number or QR data required")
    
    # Найти груз по номеру в обеих коллекциях
    cargo = db.cargo.find_one({"cargo_number": cargo_number})
    collection_name = "cargo"
    if not cargo:
        cargo = db.operator_cargo.find_one({"cargo_number": cargo_number})
        collection_name = "operator_cargo"
    
    if not cargo:
        raise HTTPException(status_code=404, detail=f"Cargo {cargo_number} not found")
    
    # Проверить, что груз на этом транспорте
    if cargo["id"] not in transport.get("cargo_list", []):
        raise HTTPException(status_code=400, detail=f"Cargo {cargo_number} is not on this transport")
    
    if cargo.get("status") != CargoStatus.ARRIVED_DESTINATION:
        raise HTTPException(status_code=400, detail="Cargo must be in arrived_destination status to place")
    
    # Автоматический выбор склада на основе привязки оператора
    available_warehouse_ids = []
    
    if current_user.role == UserRole.ADMIN:
        # Админ может размещать на любые склады
        warehouses = list(db.warehouses.find({}))
        available_warehouse_ids = [w["id"] for w in warehouses]
    else:
        # Оператор может размещать только на привязанные склады
        bindings = list(db.operator_warehouse_bindings.find({"operator_id": current_user.id}))
        available_warehouse_ids = [b["warehouse_id"] for b in bindings]
    
    if not available_warehouse_ids:
        raise HTTPException(status_code=403, detail="No available warehouses for placement")
    
    # Выбираем первый доступный склад (автоматически)
    selected_warehouse_id = available_warehouse_ids[0]
    warehouse = db.warehouses.find_one({"id": selected_warehouse_id})
    
    if not warehouse:
        raise HTTPException(status_code=404, detail="Selected warehouse not found")
    
    # Определить ячейку из QR кода ячейки или из координат
    if cell_qr_data and "ЯЧЕЙКА СКЛАДА" in cell_qr_data:
        # Парсим QR код ячейки
        try:
            lines = cell_qr_data.split("\n")
            location_line = [line for line in lines if "Местоположение:" in line][0]
            location = location_line.split("Местоположение: ")[1].strip()
            
            # Извлекаем блок, полку, ячейку из локации (например: "Склад-А-Б1-П2-Я5")
            parts = location.split("-")
            if len(parts) >= 3:
                block_number = int(parts[-3][1:])  # Убираем "Б"
                shelf_number = int(parts[-2][1:])  # Убираем "П" 
                cell_number = int(parts[-1][1:])   # Убираем "Я"
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid cell QR code format")
    
    # Проверить, что координаты ячейки указаны
    if not all([block_number, shelf_number, cell_number]):
        raise HTTPException(status_code=400, detail="Cell coordinates (block, shelf, cell) or cell QR code required")
    
    # Проверить валидность ячейки
    if (block_number > warehouse.get("blocks_count", 0) or 
        shelf_number > warehouse.get("shelves_per_block", 0) or 
        cell_number > warehouse.get("cells_per_shelf", 0)):
        raise HTTPException(status_code=400, detail="Invalid cell coordinates")
    
    # Проверить доступность ячейки
    location_code = f"{block_number}-{shelf_number}-{cell_number}"
    existing_cell = db.warehouse_cells.find_one({
        "warehouse_id": selected_warehouse_id,
        "location_code": location_code
    })
    
    if existing_cell and existing_cell.get("is_occupied", False):
        raise HTTPException(status_code=400, detail=f"Cell {location_code} is already occupied")
    
    # Размещение груза в указанную ячейку
    if existing_cell:
        # Обновить существующую ячейку
        db.warehouse_cells.update_one(
            {"_id": existing_cell["_id"]},
            {"$set": {
                "is_occupied": True,
                "cargo_id": cargo["id"],
                "placed_at": datetime.utcnow(),
                "placed_by": current_user.id,
                "updated_at": datetime.utcnow()
            }}
        )
    else:
        # Создать новую ячейку
        db.warehouse_cells.insert_one({
            "warehouse_id": selected_warehouse_id,
            "location_code": location_code,
            "block_number": block_number,
            "shelf_number": shelf_number,
            "cell_number": cell_number,
            "is_occupied": True,
            "cargo_id": cargo["id"],
            "placed_at": datetime.utcnow(),
            "placed_by": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
    
    # Обновить груз
    collection = db[collection_name]
    collection.update_one(
        {"id": cargo["id"]},
        {"$set": {
            "status": CargoStatus.IN_WAREHOUSE,
            "warehouse_id": selected_warehouse_id,
            "warehouse_location": warehouse.get("name"),
            "block_number": block_number,
            "shelf_number": shelf_number,
            "cell_number": cell_number,
            "placed_by_operator": current_user.full_name,
            "placed_by_operator_id": current_user.id,
            "placed_at": datetime.utcnow(),
            "transport_id": None,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Удалить груз из списка транспорта
    updated_cargo_list = [cid for cid in transport.get("cargo_list", []) if cid != cargo["id"]]
    new_load = max(0, transport.get("current_load_kg", 0) - cargo.get("weight", 0))
    
    # Обновить транспорт
    new_status = TransportStatus.COMPLETED if len(updated_cargo_list) == 0 else TransportStatus.ARRIVED
    db.transports.update_one(
        {"id": transport_id},
        {"$set": {
            "cargo_list": updated_cargo_list,
            "current_load_kg": new_load,
            "status": new_status,
            "completed_at": datetime.utcnow() if new_status == TransportStatus.COMPLETED else None,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Создать уведомления
    if collection_name == "cargo":
        create_personal_notification(
            cargo["sender_id"], 
            "Груз размещен на складе", 
            f"Ваш груз №{cargo['cargo_number']} размещен на складе {warehouse.get('name')} в ячейке Б{block_number}-П{shelf_number}-Я{cell_number}",
            "cargo",
            cargo["id"]
        )
    
    create_system_notification(
        "Груз размещен",
        f"Груз №{cargo['cargo_number']} размещен на складе {warehouse.get('name')} в ячейку {location_code}. Склад выбран автоматически, ячейка - {'по QR коду' if cell_qr_data else 'вручную'}",
        "cargo",
        cargo["id"],
        None,
        current_user.id
    )
    
    return {
        "message": f"Cargo {cargo['cargo_number']} successfully placed",
        "cargo_number": cargo["cargo_number"],
        "warehouse_name": warehouse.get("name"),
        "warehouse_auto_selected": True,
        "location": f"Б{block_number}-П{shelf_number}-Я{cell_number}",
        "placement_method": "cell_qr" if cell_qr_data else ("qr_number" if qr_data else "number_manual"),
        "transport_status": new_status,
        "remaining_cargo": len(updated_cargo_list)
    }

@app.delete("/api/transport/{transport_id}/remove-cargo/{cargo_id}")
async def remove_cargo_from_transport(
    transport_id: str,
    cargo_id: str,
    current_user: User = Depends(get_current_user)
):
    """Удалить груз с транспорта и вернуть его в исходное место на складе"""
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Найти транспорт
    transport = db.transports.find_one({"id": transport_id})
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    # Проверить, что транспорт не в пути
    if transport["status"] == TransportStatus.IN_TRANSIT:
        raise HTTPException(status_code=400, detail="Cannot remove cargo from transport in transit")
    
    # Найти груз в обеих коллекциях
    cargo = db.cargo.find_one({"id": cargo_id})
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": cargo_id})
        collection_name = "operator_cargo"
    else:
        collection_name = "cargo"
    
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Проверить, что груз действительно на этом транспорте
    if cargo_id not in transport.get("cargo_list", []):
        raise HTTPException(status_code=400, detail="Cargo is not on this transport")
    
    # Получить вес груза для пересчета загрузки транспорта
    cargo_weight = cargo.get("weight", 0)
    
    # Удалить груз из списка транспорта
    updated_cargo_list = [cid for cid in transport.get("cargo_list", []) if cid != cargo_id]
    new_load = max(0, transport.get("current_load_kg", 0) - cargo_weight)
    
    # Обновить транспорт
    db.transports.update_one(
        {"id": transport_id},
        {"$set": {
            "cargo_list": updated_cargo_list,
            "current_load_kg": new_load,
            "status": TransportStatus.EMPTY if new_load == 0 else transport["status"],
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Если у груза было место на складе, вернуть его туда
    if cargo.get("warehouse_id") and cargo.get("block_number") and cargo.get("shelf_number") and cargo.get("cell_number"):
        # Найти ячейку на складе
        location_code = f"{cargo['block_number']}-{cargo['shelf_number']}-{cargo['cell_number']}"
        warehouse_cell = db.warehouse_cells.find_one({
            "warehouse_id": cargo["warehouse_id"],
            "location_code": location_code
        })
        
        if warehouse_cell and not warehouse_cell.get("is_occupied", False):
            # Вернуть груз в ячейку
            db.warehouse_cells.update_one(
                {"_id": warehouse_cell["_id"]},
                {"$set": {
                    "is_occupied": True,
                    "cargo_id": cargo_id,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Обновить статус груза
            collection = db[collection_name]
            collection.update_one(
                {"id": cargo_id},
                {"$set": {
                    "status": CargoStatus.ACCEPTED,
                    "transport_id": None,
                    "updated_at": datetime.utcnow(),
                    "returned_by_operator": current_user.full_name,
                    "returned_by_operator_id": current_user.id
                }}
            )
            
            # Создать уведомление
            sender_id = cargo.get("sender_id") or cargo.get("created_by")
            if sender_id:
                create_notification(
                    sender_id, 
                    f"Груз №{cargo['cargo_number']} был возвращен на склад в исходную ячейку",
                    cargo_id
                )
            
            return {
                "message": f"Cargo {cargo['cargo_number']} successfully returned to warehouse cell {location_code}",
                "location": location_code,
                "warehouse_id": cargo["warehouse_id"]
            }
        else:
            # Ячейка занята или не найдена, просто вернуть статус на принят
            collection = db[collection_name]
            collection.update_one(
                {"id": cargo_id},
                {"$set": {
                    "status": CargoStatus.ACCEPTED,
                    "transport_id": None,
                    "warehouse_id": None,
                    "warehouse_location": None,
                    "block_number": None,
                    "shelf_number": None,
                    "cell_number": None,
                    "updated_at": datetime.utcnow(),
                    "returned_by_operator": current_user.full_name,
                    "returned_by_operator_id": current_user.id
                }}
            )
            
            # Создать уведомление
            sender_id = cargo.get("sender_id") or cargo.get("created_by")
            if sender_id:
                create_notification(
                    sender_id, 
                    f"Ваш груз №{cargo['cargo_number']} был снят с транспорта и ожидает размещения",
                    cargo_id
                )
            
            return {
                "message": f"Cargo {cargo['cargo_number']} removed from transport. Original location unavailable, cargo status set to ACCEPTED",
                "status": "accepted"
            }
    else:
        # Груз не имел места на складе, просто снять с транспорта
        collection = db[collection_name]
        collection.update_one(
            {"id": cargo_id},
            {"$set": {
                "status": CargoStatus.ACCEPTED,
                "transport_id": None,
                "updated_at": datetime.utcnow(),
                "returned_by_operator": current_user.full_name,
                "returned_by_operator_id": current_user.id
            }}
        )
        
        # Создать уведомление
        sender_id = cargo.get("sender_id") or cargo.get("created_by")
        if sender_id:
            create_notification(
                sender_id, 
                f"Ваш груз №{cargo['cargo_number']} был снят с транспорта",
                cargo_id
            )
        
        return {
            "message": f"Cargo {cargo['cargo_number']} removed from transport",
            "status": "accepted"
        }

@app.delete("/api/transport/{transport_id}")
async def delete_transport(
    transport_id: str,
    current_user: User = Depends(get_current_user)
):
    # Проверка доступа
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    transport = db.transports.find_one({"id": transport_id})
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    # Проверить, что транспорт можно удалить (не в пути)
    if transport["status"] == TransportStatus.IN_TRANSIT:
        raise HTTPException(status_code=400, detail="Cannot delete transport that is in transit")
    
    # Если есть грузы, освободить их
    if transport.get("cargo_list"):
        for cargo_id in transport["cargo_list"]:
            db.cargo.update_one(
                {"id": cargo_id},
                {"$set": {
                    "status": "accepted",  # Вернуть на склад
                    "updated_at": datetime.utcnow()
                }, "$unset": {"transport_id": ""}}
            )
    
    # Переместить транспорт в историю
    transport_history = {
        **transport,
        "deleted_at": datetime.utcnow(),
        "deleted_by": current_user.id
    }
    db.transport_history.insert_one(transport_history)
    
    # Удалить транспорт из активных
    db.transports.delete_one({"id": transport_id})
    
    return {"message": "Transport deleted and moved to history"}

# === УПРАВЛЕНИЕ ЯЧЕЙКАМИ СКЛАДА ===

@app.get("/api/warehouse/{warehouse_id}/cell/{location_code}/cargo")
async def get_cargo_in_cell(
    warehouse_id: str,
    location_code: str,
    current_user: User = Depends(get_current_user)
):
    """Получить информацию о грузе в конкретной ячейке"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Найти ячейку
    cell = db.warehouse_cells.find_one({
        "warehouse_id": warehouse_id,
        "location_code": location_code,
        "is_occupied": True
    })
    
    if not cell or not cell.get("cargo_id"):
        raise HTTPException(status_code=404, detail="No cargo found in this cell")
    
    cargo_id = cell["cargo_id"]
    
    # Найти груз в обеих коллекциях, исключая MongoDB _id
    cargo = db.cargo.find_one({"id": cargo_id}, {"_id": 0})
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": cargo_id}, {"_id": 0})
    
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    return cargo

@app.post("/api/warehouse/cargo/{cargo_id}/move")
async def move_cargo_between_cells(
    cargo_id: str,
    new_location: dict,  # {"warehouse_id", "block_number", "shelf_number", "cell_number"}
    current_user: User = Depends(get_current_user)
):
    """Перемещение груза между ячейками"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Найти груз
    cargo = db.cargo.find_one({"id": cargo_id})
    collection = db.cargo
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": cargo_id})
        collection = db.operator_cargo
    
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Проверить новое местоположение
    new_warehouse_id = new_location["warehouse_id"]
    new_block = new_location["block_number"]
    new_shelf = new_location["shelf_number"] 
    new_cell = new_location["cell_number"]
    new_location_code = f"B{new_block}-S{new_shelf}-C{new_cell}"
    
    # Проверить, свободна ли новая ячейка
    existing_cell = db.warehouse_cells.find_one({
        "warehouse_id": new_warehouse_id,
        "location_code": new_location_code,
        "is_occupied": True
    })
    
    if existing_cell:
        raise HTTPException(status_code=400, detail="Target cell is already occupied")
    
    # Освободить старую ячейку
    if cargo.get("warehouse_id") and cargo.get("block_number"):
        old_location_code = f"B{cargo['block_number']}-S{cargo['shelf_number']}-C{cargo['cell_number']}"
        db.warehouse_cells.update_one(
            {
                "warehouse_id": cargo["warehouse_id"],
                "location_code": old_location_code,
                "cargo_id": cargo_id
            },
            {"$set": {
                "is_occupied": False,
                "updated_at": datetime.utcnow()
            }, "$unset": {"cargo_id": ""}}
        )
    
    # Занять новую ячейку
    db.warehouse_cells.update_one(
        {
            "warehouse_id": new_warehouse_id,
            "location_code": new_location_code
        },
        {
            "$set": {
                "warehouse_id": new_warehouse_id,
                "location_code": new_location_code,
                "block_number": new_block,
                "shelf_number": new_shelf,
                "cell_number": new_cell,
                "is_occupied": True,
                "cargo_id": cargo_id,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    # Получить название нового склада
    new_warehouse = db.warehouses.find_one({"id": new_warehouse_id})
    new_warehouse_name = new_warehouse["name"] if new_warehouse else "Неизвестный склад"
    
    # Обновить груз
    collection.update_one(
        {"id": cargo_id},
        {"$set": {
            "warehouse_location": f"{new_warehouse_name} - Блок {new_block}, Полка {new_shelf}, Ячейка {new_cell}",
            "warehouse_id": new_warehouse_id,
            "block_number": new_block,
            "shelf_number": new_shelf,
            "cell_number": new_cell,
            "updated_at": datetime.utcnow(),
            "placed_by_operator": current_user.full_name,
            "placed_by_operator_id": current_user.id
        }}
    )
    
    return {"message": "Cargo moved successfully", "new_location": new_location_code}

@app.delete("/api/warehouse/cargo/{cargo_id}/remove")
async def remove_cargo_from_cell(
    cargo_id: str,
    current_user: User = Depends(get_current_user)
):
    """Удалить груз из ячейки (освободить ячейку)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Найти груз
    cargo = db.cargo.find_one({"id": cargo_id})
    collection = db.cargo
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": cargo_id})
        collection = db.operator_cargo
    
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Освободить ячейку
    if cargo.get("warehouse_id") and cargo.get("block_number"):
        location_code = f"B{cargo['block_number']}-S{cargo['shelf_number']}-C{cargo['cell_number']}"
        db.warehouse_cells.update_one(
            {
                "warehouse_id": cargo["warehouse_id"],
                "location_code": location_code,
                "cargo_id": cargo_id
            },
            {"$set": {
                "is_occupied": False,
                "updated_at": datetime.utcnow()
            }, "$unset": {"cargo_id": ""}}
        )
    
    # Обновить груз (убрать местоположение)
    collection.update_one(
        {"id": cargo_id},
        {"$set": {
            "status": "accepted",  # Вернуть в статус "принят"
            "updated_at": datetime.utcnow()
        }, "$unset": {
            "warehouse_location": "",
            "warehouse_id": "",
            "block_number": "",
            "shelf_number": "",
            "cell_number": ""
        }}
    )
    
    return {"message": "Cargo removed from cell successfully"}

@app.get("/api/cargo/{cargo_id}/details")
async def get_cargo_details(
    cargo_id: str,
    current_user: User = Depends(get_current_user)
):
    """Получить полную информацию о грузе"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Найти груз в обеих коллекциях, исключая MongoDB _id
    cargo = db.cargo.find_one({"id": cargo_id}, {"_id": 0})
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": cargo_id}, {"_id": 0})
    
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    return cargo

@app.put("/api/cargo/{cargo_id}/update")
async def update_cargo_details(
    cargo_id: str,
    update_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Обновить информацию о грузе"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Найти груз в обеих коллекциях
    cargo = db.cargo.find_one({"id": cargo_id})
    collection = db.cargo
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": cargo_id})
        collection = db.operator_cargo
    
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Фильтровать разрешенные поля для обновления
    allowed_fields = [
        "cargo_name", "description", "weight", "declared_value",
        "sender_full_name", "sender_phone", "recipient_full_name", 
        "recipient_phone", "recipient_address", "status"
    ]
    
    filtered_update = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if not filtered_update:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    # Добавить информацию об обновлении
    filtered_update["updated_at"] = datetime.utcnow()
    filtered_update["updated_by_operator"] = current_user.full_name
    filtered_update["updated_by_operator_id"] = current_user.id
    
    # Обновить груз
    collection.update_one(
        {"id": cargo_id},
        {"$set": filtered_update}
    )
    
    return {"message": "Cargo updated successfully"}

# === API ДЛЯ ТРЕКИНГА ГРУЗА КЛИЕНТАМИ И УВЕДОМЛЕНИЙ ===

@app.post("/api/cargo/tracking/create")
async def create_cargo_tracking(
    tracking_data: CargoTrackingCreate,
    current_user: User = Depends(get_current_user)
):
    """Создать трекинг код для груза"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Найти груз по номеру
    cargo = db.cargo.find_one({"cargo_number": tracking_data.cargo_number})
    if not cargo:
        cargo = db.operator_cargo.find_one({"cargo_number": tracking_data.cargo_number})
        if not cargo:
            raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Проверить существующий трекинг
    existing_tracking = db.cargo_tracking.find_one({"cargo_id": cargo["id"]})
    if existing_tracking:
        return {
            "message": "Tracking already exists",
            "tracking_code": existing_tracking["tracking_code"],
            "cargo_number": cargo["cargo_number"]
        }
    
    # Создать уникальный трекинг код
    tracking_code = f"TRK{cargo['cargo_number']}{str(uuid.uuid4())[-8:].upper()}"
    
    tracking_id = str(uuid.uuid4())
    tracking = {
        "id": tracking_id,
        "cargo_id": cargo["id"],
        "cargo_number": cargo["cargo_number"],
        "tracking_code": tracking_code,
        "client_phone": tracking_data.client_phone,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "access_count": 0
    }
    
    db.cargo_tracking.insert_one(tracking)
    
    # Добавить в историю груза
    add_cargo_history(
        cargo["id"],
        cargo["cargo_number"],
        "tracking_created",
        None,
        None,
        tracking_code,
        f"Создан трекинг код для клиента {tracking_data.client_phone}",
        current_user.id,
        current_user.full_name,
        current_user.role,
        {"tracking_code": tracking_code, "client_phone": tracking_data.client_phone}
    )
    
    return {
        "message": "Tracking created successfully",
        "tracking_code": tracking_code,
        "cargo_number": cargo["cargo_number"],
        "client_phone": tracking_data.client_phone
    }

@app.get("/api/debug/tracking/{tracking_code}")
async def debug_tracking(tracking_code: str):
    """Debug tracking lookup"""
    try:
        # Найти трекинг
        tracking = db.cargo_tracking.find_one({"tracking_code": tracking_code, "is_active": True})
        if not tracking:
            return {"error": "Tracking code not found", "tracking_code": tracking_code}
        
        # Попробовать найти груз в обеих коллекциях
        cargo_in_cargo = db.cargo.find_one({"id": tracking["cargo_id"]})
        cargo_in_operator = db.operator_cargo.find_one({"id": tracking["cargo_id"]})
        
        return {
            "tracking_code": tracking_code,
            "cargo_id": str(tracking["cargo_id"]),
            "cargo_number": str(tracking["cargo_number"]),
            "cargo_in_cargo_collection": cargo_in_cargo is not None,
            "cargo_in_operator_collection": cargo_in_operator is not None,
            "cargo_found": (cargo_in_cargo is not None) or (cargo_in_operator is not None)
        }
    except Exception as e:
        return {"error": f"Exception: {str(e)}", "tracking_code": tracking_code}

@app.get("/api/cargo/track/{tracking_code}")
async def track_cargo_by_code(tracking_code: str):
    """Публичный трекинг груза по коду (без авторизации)"""
    try:
        # Найти трекинг
        tracking = db.cargo_tracking.find_one({"tracking_code": tracking_code, "is_active": True})
        if not tracking:
            raise HTTPException(status_code=404, detail="Tracking code not found")
        
        # Найти груз
        cargo = db.cargo.find_one({"id": tracking["cargo_id"]})
        if not cargo:
            cargo = db.operator_cargo.find_one({"id": tracking["cargo_id"]})
            if not cargo:
                raise HTTPException(status_code=404, detail="Cargo not found")
        
        # Обновить счетчик доступа
        db.cargo_tracking.update_one(
            {"id": tracking["id"]},
            {"$set": {"last_accessed": datetime.utcnow()}, "$inc": {"access_count": 1}}
        )
        
        # Получить информацию о складе и транспорте
        warehouse_info = None
        if cargo.get("warehouse_id"):
            warehouse = db.warehouses.find_one({"id": cargo["warehouse_id"]})
            if warehouse:
                warehouse_info = {
                    "name": warehouse["name"],
                    "location": warehouse["location"]
                }
        
        transport_info = None
        if cargo.get("transport_id"):
            transport = db.transports.find_one({"id": cargo["transport_id"]})
            if transport:
                transport_info = {
                    "transport_number": transport["transport_number"],
                    "driver_name": transport["driver_name"],
                    "direction": transport["direction"],
                    "status": transport["status"]
                }
        
        # Получить последние записи истории (публичные только)
        recent_history = list(db.cargo_history.find(
            {"cargo_id": cargo["id"], "action_type": {"$in": ["created", "status_changed", "placed_on_transport", "dispatched", "arrived"]}},
            {"_id": 0, "action_type": 1, "description": 1, "change_date": 1}
        ).sort("change_date", -1).limit(10))
        
        # Serialize all MongoDB documents to avoid ObjectId issues
        serialized_cargo = serialize_mongo_document(cargo)
        serialized_warehouse_info = serialize_mongo_document(warehouse_info) if warehouse_info else None
        serialized_transport_info = serialize_mongo_document(transport_info) if transport_info else None
        recent_history = serialize_mongo_document(recent_history)
        
        return {
            "tracking_code": tracking_code,
            "cargo_number": serialized_cargo["cargo_number"],
            "cargo_name": serialized_cargo.get("cargo_name", "Груз"),
            "status": serialized_cargo["status"],
            "weight": serialized_cargo.get("weight", 0),
            "created_at": serialized_cargo["created_at"],
            "sender_full_name": serialized_cargo.get("sender_full_name", "Не указан"),
            "recipient_full_name": serialized_cargo.get("recipient_full_name", serialized_cargo.get("recipient_name", "Не указан")),
            "recipient_address": serialized_cargo.get("recipient_address", ""),
            "current_location": {
                "warehouse": serialized_warehouse_info,
                "transport": serialized_transport_info,
                "description": _get_location_description(serialized_cargo)
            },
            "recent_history": recent_history,
            "last_updated": serialized_cargo.get("updated_at", serialized_cargo["created_at"])
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log other exceptions and return a generic error
        print(f"Error in track_cargo_by_code: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/notifications/client/send")
async def send_client_notification(
    notification_data: ClientNotificationCreate,
    current_user: User = Depends(get_current_user)
):
    """Отправить уведомление клиенту"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Найти груз
    cargo = db.cargo.find_one({"id": notification_data.cargo_id})
    if not cargo:
        cargo = db.operator_cargo.find_one({"id": notification_data.cargo_id})
        if not cargo:
            raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Создать уведомление
    notification_id = str(uuid.uuid4())
    notification = {
        "id": notification_id,
        "cargo_id": notification_data.cargo_id,
        "cargo_number": cargo["cargo_number"],
        "client_phone": notification_data.client_phone,
        "notification_type": notification_data.notification_type,
        "message_text": notification_data.message_text,
        "status": "pending",
        "created_by": current_user.id,
        "created_at": datetime.utcnow()
    }
    
    db.client_notifications.insert_one(notification)
    
    # Здесь будет интеграция с SMS/Email/WhatsApp сервисами
    # Пока что помечаем как отправленное
    db.client_notifications.update_one(
        {"id": notification_id},
        {"$set": {"status": "sent", "sent_at": datetime.utcnow()}}
    )
    
    # Добавить в историю груза
    add_cargo_history(
        notification_data.cargo_id,
        cargo["cargo_number"],
        "client_notification_sent",
        None,
        None,
        notification_data.notification_type,
        f"Отправлено {notification_data.notification_type} уведомление клиенту {notification_data.client_phone}",
        current_user.id,
        current_user.full_name,
        current_user.role,
        {"notification_id": notification_id, "message_preview": notification_data.message_text[:50]}
    )
    
    return {
        "message": "Notification sent successfully",
        "notification_id": notification_id,
        "cargo_number": cargo["cargo_number"],
        "notification_type": notification_data.notification_type
    }

@app.post("/api/messages/internal/send")
async def send_internal_message(
    message_data: InternalMessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Отправить внутреннее сообщение другому оператору"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Проверить существование получателя
    recipient = db.users.find_one({"id": message_data.recipient_id})
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    if recipient["role"] not in [UserRole.ADMIN.value, UserRole.WAREHOUSE_OPERATOR.value]:
        raise HTTPException(status_code=400, detail="Can only send messages to admins and operators")
    
    # Проверить груз если указан
    cargo_number = None
    if message_data.related_cargo_id:
        cargo = db.cargo.find_one({"id": message_data.related_cargo_id})
        if not cargo:
            cargo = db.operator_cargo.find_one({"id": message_data.related_cargo_id})
        if cargo:
            cargo_number = cargo["cargo_number"]
    
    # Создать сообщение
    message_id = str(uuid.uuid4())
    message = {
        "id": message_id,
        "sender_id": current_user.id,
        "sender_name": current_user.full_name,
        "recipient_id": message_data.recipient_id,
        "recipient_name": recipient["full_name"],
        "message_subject": message_data.message_subject,
        "message_text": message_data.message_text,
        "priority": message_data.priority,
        "related_cargo_id": message_data.related_cargo_id,
        "related_cargo_number": cargo_number,
        "is_read": False,
        "sent_at": datetime.utcnow()
    }
    
    db.internal_messages.insert_one(message)
    
    # Создать уведомление для получателя
    create_notification(
        message_data.recipient_id,
        f"Новое сообщение от {current_user.full_name}: {message_data.message_subject}",
        message_data.related_cargo_id
    )
    
    return {
        "message": "Internal message sent successfully",
        "message_id": message_id,
        "recipient_name": recipient["full_name"]
    }

@app.get("/api/messages/internal/inbox")
async def get_internal_messages_inbox(
    current_user: User = Depends(get_current_user)
):
    """Получить входящие внутренние сообщения"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    messages = list(db.internal_messages.find(
        {"recipient_id": current_user.id},
        {"_id": 0}
    ).sort("sent_at", -1))
    
    unread_count = db.internal_messages.count_documents({
        "recipient_id": current_user.id,
        "is_read": False
    })
    
    return {
        "messages": messages,
        "total_messages": len(messages),
        "unread_count": unread_count
    }

@app.put("/api/messages/internal/{message_id}/read")
async def mark_internal_message_read(
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """Отметить внутреннее сообщение как прочитанное"""
    if current_user.role not in [UserRole.ADMIN, UserRole.WAREHOUSE_OPERATOR]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = db.internal_messages.update_one(
        {"id": message_id, "recipient_id": current_user.id},
        {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return {"message": "Message marked as read"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)