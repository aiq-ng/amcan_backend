from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from shared.db import init_db
from shared.schema import create_tables
from shared.seed import seed_data
from modules.auth.router import router as auth_router
from modules.feeds.router import router as feed_router
from modules.doctors.router import router as doctors_router
from modules.appointments.router import router as appointments_router
from modules.chat.router import router as chat_router
from modules.video_call.router import router as video_call_router

app = FastAPI(title="Mental Health Therapy App")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(feed_router, prefix="/feed", tags=["feed"])
app.include_router(doctors_router, prefix="/doctors", tags=["doctors"])
app.include_router(appointments_router, prefix="/appointments", tags=["appointments"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(video_call_router, prefix="/video-call", tags=["video-call"])

@app.on_event("startup")
async def startup_event():
    await init_db()
    await create_tables()
    await seed_data()

@app.get("/")
async def root():
    return {"message": "Welcome to the amcan App"}