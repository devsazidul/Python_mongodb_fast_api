from fastapi import FastAPI
from typing import List
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import certifi

# rabbiking00
# rQauiItdlNdL7hdX

app = FastAPI()

MONGO_URL = "mongodb+srv://sazidul:sazidul123@cluster0.z6b9l.mongodb.net/python?retryWrites=true&w=majority&ssl=true"
DB_NAME = "mydatabase"
COLLECTION_NAME = "user_data"


# MongoDB client initialization on startup
@app.on_event("startup")
async def startup_db():
    app.client = AsyncIOMotorClient(MONGO_URL, tlsCAFile=certifi.where())  # Initialize once with SSL
    app.db = app.client[DB_NAME]
    app.collection = app.db[COLLECTION_NAME]


# Close the MongoDB connection on shutdown
@app.on_event("shutdown")
async def shutdown_db():
    app.client.close()


class Data(BaseModel):
    fullname: str
    schoolname: str
    role: str
    age: int

@app.post("/postdata")
async def postdata(data: Data):
    user_data = data.dict() 
    result = await app.collection.insert_one(user_data) 
    return {"message": "data added successfully", "id": str(result.inserted_id)}


@app.get("/getdata", response_model=List[Data])
async def getdata():
    users = []
    async for user in app.collection.find():
        user['_id'] = str(user['_id'])
        users.append(user)
    return users
