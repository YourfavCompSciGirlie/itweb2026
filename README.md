# itweb2026
# AegisAI — Hybrid Fraud Detection System
> ITWeb Hackathon 2026

AegisAI is a real-time fraud detection system combining SIM Swap verification and Graph Neural Network analysis to protect banking transactions.

---

## Team Roles
| Person        | Responsibility |
|-------------  |--------------- |
| Lady Amahle   | Backend API, SIM Swap wrapper, Risk Engine, Integration |
| Lady Matshepo | GNN fraud graph detection |
| Lady Malaika  | USSD simulator + branch verification layer |
| Lady Toby     | Streamlit dashboard |
| Gentleman     | Streamlit dashboard + HuggingFace model research |

---

## Project Structure
aegisai/
├── backend/          # FastAPI backend (Nylon)
├── frontend/         # Streamlit dashboard (Lady Toby + Gentleman)
├── ussd_simulator/   # USSD mock server (Lady Malaika)
├── database/         # SQL migrations (already run on Supabase)
├── tests/            # Unit tests
└── docs/             # Architecture + documentation

---

## Getting Started (Everyone does this)

### 1. Clone the repo
```bash
git clone https://github.com/YourfavCompSciGirlie/itweb2026.git
cd itweb2026
```

### 2. Install backend dependencies
```bash
cd backend
pip install fastapi uvicorn pydantic python-dotenv httpx supabase python-multipart --user
```

### 3. Set up environment variables
Copy the example env file and fill in the values (get from Nylon):
```bash
cp .env.example .env
```

### 4. Run the backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 5. Confirm it works
Open browser at:
- http://127.0.0.1:8000 — health check
- http://127.0.0.1:8000/docs — live API docs

---

## API Endpoints

### POST /api/risk-score
Takes a transaction and returns a fraud risk decision.

**Request:**
```json
{
  "phone_hash": "abc123",
  "amount": 15000.00,
  "recipient_phone_hash": "xyz789",
  "channel": "USSD",
  "sim_swap_minutes_ago": 45,
  "gnn_fraud_score": 72.0
}
```

**Response:**
```json
{
  "risk_score": 85,
  "decision": "BLOCK",
  "reason": "SIM swapped 45 mins ago (CRITICAL) | Very large amount: R15000.00 | GNN flagged recipient network (score: 72)"
}
```

### POST /api/simswap-check
Checks SIM swap status for a phone number.

**Request:**
```json
{
  "phone_number": "+27821234567"
}
```

**Response:**
```json
{
  "phone_number": "+27821234567",
  "swapped": true,
  "minutes_ago": 45,
  "source": "mock"
}
```

### GET /api/transactions/recent
Returns the 20 most recent transactions from the database.

---

## What Each Person Builds Tomorrow

### Lady Matshepo — GNN Graph Input
- Build graph input in `backend/app/services/gnn_detector.py`
- Your function must return a fraud score 0-100
- Expected output format:
```python
{"account_id": "xxx", "fraud_score": 72.5, "flagged": True}
```

### Lady Malaika — USSD Simulator
- Build in `ussd_simulator/ussd_server.py`
- Mock the USSD menu flow
- When a transaction is submitted, call `POST /api/risk-score`

### Lady Toby + Gentleman — Streamlit Dashboard
- Build in `frontend/streamlit_app.py`
- Call `GET /api/transactions/recent` to show transaction list
- Call `POST /api/risk-score` to test a transaction live
- Backend runs on `http://127.0.0.1:8000`

---

## Environment Variables (get from Lady Amahle)
SUPABASE_URL=
SUPABASE_ANON_KEY=
VONAGE_API_KEY=
VONAGE_API_SECRET=
APP_SECRET_KEY=