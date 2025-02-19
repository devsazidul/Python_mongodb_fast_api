from fastapi import FastAPI
from typing import List
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import certifi

app = FastAPI()

MONGO_URL = "mongodb+srv://sazidul:sazidul123@cluster0.z6b9l.mongodb.net/python?retryWrites=true&w=majority&ssl=true"
DB_NAME = "mydatabase"

# MongoDB client initialization on startup
@app.on_event("startup")
async def startup_db():
    app.client = AsyncIOMotorClient(MONGO_URL, tlsCAFile=certifi.where())  # Initialize once with SSL
    app.db = app.client[DB_NAME]


# Close the MongoDB connection on shutdown
@app.on_event("shutdown")
async def shutdown_db():
    app.client.close()

# --- Models ---
class PersonalInfo(BaseModel):
    fullname: str
    age: int
    address: str
    phone_number: str

class ClientDetails(BaseModel):
    client_name: str
    company: str
    email: str
    phone: str

class ProductionName(BaseModel):
    product_name: str
    description: str
    launch_date: str

# --- POST Routes ---
@app.post("/person")
async def post_personal_info(data: PersonalInfo):
    personal_data = data.dict()
    collection = app.db["personal_info"]  # Collection for Personal Info
    result = await collection.insert_one(personal_data)
    return {"message": "Personal Information added successfully", "id": str(result.inserted_id)}

@app.post("/client")
async def post_client_details(data: ClientDetails):
    client_data = data.dict()
    collection = app.db["client_details"]  # Collection for Client Details
    result = await collection.insert_one(client_data)
    return {"message": "Client Details added successfully", "id": str(result.inserted_id)}

@app.post("/product")
async def post_production_name(data: ProductionName):
    production_data = data.dict()
    collection = app.db["production_name"]  # Collection for Production Name
    result = await collection.insert_one(production_data)
    return {"message": "Production Name added successfully", "id": str(result.inserted_id)}

# --- GET Routes ---
@app.get("/person", response_model=List[PersonalInfo])
async def get_personal_info():
    collection = app.db["personal_info"]
    users = []
    async for user in collection.find():
        user['_id'] = str(user['_id'])
        users.append(user)
    return users

@app.get("/client", response_model=List[ClientDetails])
async def get_client_details():
    collection = app.db["client_details"]
    clients = []
    async for client in collection.find():
        client['_id'] = str(client['_id'])
        clients.append(client)
    return clients

@app.get("/product", response_model=List[ProductionName])
async def get_production_name():
    collection = app.db["production_name"]
    products = []
    async for product in collection.find():
        product['_id'] = str(product['_id'])
        products.append(product)
    return products
