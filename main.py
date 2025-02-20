# (pip install fastapi uvicorn django stripe) Payment mathod installation package.
import os
from dotenv import load_dotenv
from fastapi import FastAPI ,HTTPException
from typing import List, Optional
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
from bson import ObjectId  # ✅ Import ObjectId for MongoDB
import stripe
# rabbiking00
# rQauiItdlNdL7hdX

app = FastAPI()

MONGO_URL = "mongodb+srv://sazidul:sazidul123@cluster0.z6b9l.mongodb.net/python?retryWrites=true&w=majority&ssl=true"
DB_NAME = "mydatabase"
COLLECTION_NAME = "user_data"

# publish_key="pk_test_51QUQaVRsWBiTKSlUvFbcre2Ib6ivd4X89YucdbrOh78iZ1S1eGSC9PmC8RSU9u2a58onRYciytAuKMsI76n4L3e300CvMv7PHG"
# secret_key="sk_test_51QUQaVRsWBiTKSlUs13riCunoMVaUOWxVT5ykhYN1c7tyK4uFD8iGwr2fV7GsSQdjn69d6HTWXHGBdBnXy5uG6Ed000g5uEa1X"


# Stripe api key akhane load kora hoice are .env file are modde stripe are api key rakha hoice.
load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

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

class PaymentData(BaseModel):
    amount: int
    currency: str ="usd"
    description: Optional[str] = None
    card_number:str
    exp_month:str
    exp_year:str
    cvc:str



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


@app.put("/putdata/{id}")
async def putdata(id:str, data:Data):   
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code= 400 ,detail='Invalid objectid values')
    user_data=data.dict()
    result=await app.collection.update_one({"_id":ObjectId(id)},{"$set":user_data})
    if result.matched_count==0:
        raise HTTPException(status_code= 404,detail="User not found")
    return {"Message":"data update successfully"}

@app.delete("/postdelete/{id}")
async def deletedata(id:str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code= 400, detail='Invalid object formate')
    result = await app.collection.delete_one({"_id":ObjectId(id)})
    if result.deleted_count ==0:
        raise HTTPException(status_code= 404,detail='User not found')
    return {"Message":"delete data successful"}

Payment_collection_name="payment"
@app.post("/createpayment")
async def create_payment_intent(payment: PaymentData):
    try:
        payment_mathod=stripe.PaymentMethod.create(
            type= "card",
            card={
                "number":payment.card_number,
                "exp_month":payment.exp_month,
                "exp_year":payment.exp_year,
                "cvc":payment.cvc
            },
        )
        # Create a PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=payment.amount,  # Amount in cents
            currency=payment.currency,
            description=payment.description,
            payment_method=payment_mathod.id,
            confirm=True,
        )
        # Store payment intent details in MongoDB
        payment_record = {
            "payment_intent_id": intent.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": intent.status,
            "card_number":payment.card_number,
        }
        await app.db["Payment_collection_name"].insert_one(payment_record)
        return {"client_secret": intent.client_secret}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/paymentdone")
async def confirm_payment(payment_intent_id: str):
    try:
        # Retrieve the PaymentIntent
        intent = stripe.PaymentIntent.retrieve(payment_intent_id    )
        if intent.status == "succeeded":
            # Update payment status in MongoDB
            await app.collection.update_one(
                {"payment_intent_id": payment_intent_id},
                {"$set": {"status": "succeeded"}}
            )
            return {"status": "success", "message": "Payment succeeded!"}
        else:
            return {"status": "failed", "message": "Payment not succeeded."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))