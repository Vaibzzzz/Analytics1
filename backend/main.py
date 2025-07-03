from fastapi import FastAPI
from API import API_Dashboard
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS (adjust origins if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(API_Dashboard.router)
