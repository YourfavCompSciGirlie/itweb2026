from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import transaction, simswap

app = FastAPI(
    title="AegisAI Fraud Detection API",
    description="Hybrid SIM Swap + GNN fraud detection backend",
    version="1.0.0"
)

# Allow Streamlit frontend and USSD simulator to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(transaction.router, prefix="/api", tags=["Transactions"])
app.include_router(simswap.router, prefix="/api", tags=["SIM Swap"])

@app.get("/")
async def root():
    return {"status": "AegisAI backend is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}