from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app import router
import os

app = FastAPI()
os.makedirs("data/output", exist_ok=True)
# Mount static directory for serving results
app.mount("/data/output", StaticFiles(directory="data/output"), name="output")

# Include router
# app.include_router(router)