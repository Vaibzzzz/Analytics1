from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from kpi_logic import compute_all_kpis

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
        print("Uploaded columns:", df.columns.tolist())
        kpis = compute_all_kpis(df)
        return {"success": True, "kpis": kpis}
    except Exception as e:
        print("Error:", e)
        return {"success": False, "error": str(e)}
