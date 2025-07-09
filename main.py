import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'), # type: ignore
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
    "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
    "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_CERT_URL'),
    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL'),
    "universe_domain": os.getenv('FIREBASE_UNIVERSE_DOMAIN')
    # Add any other required fields from the service account JSON
})
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://smart-energy-27ef0-default-rtdb.firebaseio.com'
})

app = FastAPI()

class IoTMeasurement(BaseModel):
    current: float
    voltage: float
    power: float
    device_id: str
    timestamp: Optional[datetime] = None

@app.post("/iot/measurements")
async def receive_measurement(measurement: IoTMeasurement):
    try:
        # Basic validation for non-negative values
        if measurement.current < 0 or measurement.voltage < 0 or measurement.power < 0:
            raise HTTPException(status_code=400, detail="Measurements cannot be negative")
        
        # If no timestamp provided, set to current time
        if not measurement.timestamp:
            measurement.timestamp = datetime.utcnow()
        
        # Prepare data for Firebase
        data = {
            'current': measurement.current,
            'voltage': measurement.voltage,
            'power': measurement.power,
            'device_id': measurement.device_id,
            'timestamp': measurement.timestamp.isoformat()
        }
        
        # Save to Firebase Realtime Database
        ref = db.reference(f'/measurements/{measurement.device_id}')
        new_measurement_ref = ref.push(data) # type: ignore
        
        # Prepare response
        response = {
            "status": "success",
            "received_data": data,
            "firebase_key": new_measurement_ref.key
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing measurement: {str(e)}")