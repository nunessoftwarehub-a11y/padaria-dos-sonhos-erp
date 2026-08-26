from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
import bcrypt
import jwt
import secrets
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
ROLE_LABELS = {"admin": "Administrador", "cashier": "Caixa", "staff": "Funcionário"}


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class AuthInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: Optional[str] = None

class ForgotInput(BaseModel):
    email: EmailStr

class ProductInput(BaseModel):
    name: str = Field(min_length=2)
    category: str = "Salgados"
    sale_price: Optional[float] = None
    purchase_price: Optional[float] = None
    purchase_quantity: Optional[float] = None
    unit: Optional[str] = None
    barcode: Optional[str] = None

class IngredientInput(BaseModel):
    name: str = Field(min_length=2)
    purchase_price: float = Field(ge=0)
    purchase_quantity: float = Field(gt=0)
    unit: str = "unidade"

class CustomerInput(BaseModel):
    name: str = Field(min_length=2)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class RecipeInput(BaseModel):
    name: str = Field(min_length=2)
    category: Optional[str] = None
    ingredients: Optional[List[dict]] = None
    preparation: Optional[str] = None
    duration_minutes: Optional[int] = None
    yield_quantity: Optional[float] = None

class SaleItemInput(BaseModel):
    product_name: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)

class SaleInput(BaseModel):
    product_name: Optional[str] = None
    quantity: Optional[float] = None
    items: Optional[List[SaleItemInput]] = None
    total: Optional[float] = None
    payment_method: Optional[str] = None
    customer_name: Optional[str] = None
    customer_document: Optional[str] = None
    print_receipt: bool = False

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    role_label: str

def hash_password(value: str) -> str:
    return bcrypt.hashpw(value.encode(), bcrypt.gensalt()).decode()

def public_user(user: dict) -> UserResponse:
    return UserResponse(id=str(user["id"]), name=user["name"], email=user["email"], role=user["role"], role_label=ROLE_LABELS[user["role"]])

def issue_token(user: dict) -> str:
    return jwt.encode({"sub": user["id"], "exp": datetime.now(timezone.utc).timestamp() + 900, "type": "access"}, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def current_user(request: Request) -> UserResponse:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else None
    if not token:
        raise HTTPException(status_code=401, detail="Sessão expirada")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return public_user(user)
    except (jwt.InvalidTokenError, KeyError):
        raise HTTPException(status_code=401, detail="Sessão inválida")

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"service": "Padaria dos Sonhos ERP", "status": "online"}

@api_router.post("/auth/register", response_model=UserResponse)
async def register(input: AuthInput, response: Response):
    email = input.email.lower()
    if await db.users.find_one({"email": email}, {"_id": 0}):
        raise HTTPException(status_code=409, detail="Este e-mail já está cadastrado")
    user = {"id": str(uuid.uuid4()), "name": input.name or email.split("@")[0].title(), "email": email, "password_hash": hash_password(input.password), "role": "staff", "created_at": datetime.now(timezone.utc).isoformat()}
    await db.users.insert_one(user)
    response.set_cookie("access_token", issue_token(user), httponly=True, samesite="lax", max_age=900)
    return public_user(user)

@api_router.post("/auth/login", response_model=UserResponse)
async def login(input: AuthInput, response: Response):
    identifier = input.email.lower()
    attempt = await db.login_attempts.find_one({"identifier": identifier}, {"_id": 0})
    now = datetime.now(timezone.utc)
    if attempt and attempt.get("locked_until") and datetime.fromisoformat(attempt["locked_until"]) > now:
        raise HTTPException(status_code=429, detail="Muitas tentativas. Tente novamente em alguns minutos")
    user = await db.users.find_one({"email": identifier}, {"_id": 0})
    if not user or not bcrypt.checkpw(input.password.encode(), user["password_hash"].encode()):
        failures = (attempt or {}).get("failures", 0) + 1
        update = {"identifier": identifier, "failures": failures, "updated_at": now.isoformat()}
        if failures >= 5:
            update["locked_until"] = (now + __import__('datetime').timedelta(minutes=15)).isoformat()
        await db.login_attempts.update_one({"identifier": identifier}, {"$set": update}, upsert=True)
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
    await db.login_attempts.delete_one({"identifier": identifier})
    response.set_cookie("access_token", issue_token(user), httponly=True, samesite="lax", max_age=900)
    return public_user(user)

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Sessão encerrada"}

@api_router.get("/auth/me", response_model=UserResponse)
async def me(user: UserResponse = Depends(current_user)):
    return user

@api_router.post("/auth/forgot-password")
async def forgot_password(input: ForgotInput):
    return {"message": "Se o e-mail existir, enviaremos as instruções de recuperação."}

@api_router.get("/dashboard", dependencies=[Depends(current_user)])
async def dashboard():
    return {"metrics": [], "sales": [], "inventory": []}

async def list_resource(collection: str, user: UserResponse):
    return await db[collection].find({"created_by": user.id}, {"_id": 0}).sort("created_at", -1).to_list(100)

async def create_resource(collection: str, payload: BaseModel, user: UserResponse):
    document = payload.model_dump() if isinstance(payload, BaseModel) else dict(payload)
    document.update({"id": str(uuid.uuid4()), "created_by": user.id, "created_at": datetime.now(timezone.utc).isoformat()})
    await db[collection].insert_one(document)
    document.pop("_id", None)
    return document

@api_router.get("/products")
async def products(user: UserResponse = Depends(current_user)):
    return await list_resource("products", user)

@api_router.post("/products")
async def create_product(input: ProductInput, user: UserResponse = Depends(current_user)):
    document = input.model_dump()
    if input.purchase_price is not None and input.purchase_quantity:
        cost = input.purchase_price / input.purchase_quantity
        document["unit_cost"] = round(cost, 4)
        document["suggested_sale_price"] = round(cost * 2.5, 2)
    return await create_resource("products", document, user)

@api_router.get("/ingredients")
async def ingredients(user: UserResponse = Depends(current_user)):
    return await list_resource("ingredients", user)

@api_router.post("/ingredients")
async def create_ingredient(input: IngredientInput, user: UserResponse = Depends(current_user)):
    document = input.model_dump()
    document["unit_cost"] = round(input.purchase_price / input.purchase_quantity, 4)
    return await create_resource("ingredients", document, user)

@api_router.get("/customers")
async def customers(user: UserResponse = Depends(current_user)):
    return await list_resource("customers", user)

@api_router.post("/customers")
async def create_customer(input: CustomerInput, user: UserResponse = Depends(current_user)):
    return await create_resource("customers", input, user)

@api_router.get("/recipes")
async def recipes(user: UserResponse = Depends(current_user)):
    return await list_resource("recipes", user)

@api_router.post("/recipes")
async def create_recipe(input: RecipeInput, user: UserResponse = Depends(current_user)):
    document = input.model_dump()
    total_cost = 0
    for line in input.ingredients or []:
        ingredient = await db.ingredients.find_one({"id": line.get("ingredient_id"), "created_by": user.id}, {"_id": 0})
        if ingredient:
            total_cost += float(ingredient["unit_cost"]) * float(line.get("quantity", 0))
    document["cost_total"] = round(total_cost, 2)
    document["cost_per_unit"] = round(total_cost / input.yield_quantity, 2) if input.yield_quantity else total_cost
    return await create_resource("recipes", document, user)

@api_router.get("/sales")
async def sales(user: UserResponse = Depends(current_user)):
    return await list_resource("sales", user)

@api_router.post("/sales")
async def create_sale(input: SaleInput, user: UserResponse = Depends(current_user)):
    document = input.model_dump()
    if input.items:
        document["items"] = [item.model_dump() for item in input.items]
        document["total"] = round(sum(item.quantity * item.unit_price for item in input.items), 2)
        document["quantity"] = sum(item.quantity for item in input.items)
        extras = len(input.items) - 1
        document["product_name"] = input.items[0].product_name if extras == 0 else f"{input.items[0].product_name} +{extras}"
    elif not input.product_name:
        raise HTTPException(status_code=422, detail="Informe os itens da venda")
    return await create_resource("sales", document, user)

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[os.environ['FRONTEND_URL']],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()