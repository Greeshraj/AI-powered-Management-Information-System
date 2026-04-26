# Business Analytics Dashboard

A full-stack analytics app — upload a CSV and get instant revenue insights + charts.

## Project Structure

```
analytics-dashboard/
├── backend/
│   ├── main.py            # FastAPI server
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Main React component
│   │   ├── index.css      # Styles
│   │   └── main.jsx       # Entry point
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── sample_data.csv        # Test file
```

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API will be live at: http://localhost:8000  
Swagger docs at: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App will be live at: http://localhost:3000

## CSV Format

Your CSV must include these columns:

| Column     | Type     | Example      |
|------------|----------|--------------|
| Date       | date     | 2024-01-15   |
| Region     | string   | North        |
| Product    | string   | Widget A     |
| Revenue    | number   | 12000        |
| Cost       | number   | 7000         |
| Marketing  | number   | 1500         |

## API Endpoints

| Method | Path      | Description              |
|--------|-----------|--------------------------|
| POST   | /upload   | Upload CSV, get insights |
| GET    | /health   | Health check             |

### Sample Response

```json
{
  "insights": [
    "Total Revenue: $201,500.00",
    "Total Cost: $114,400.00",
    "Total Profit: $87,100.00",
    "Profit Margin: 43.2%",
    ...
  ],
  "monthly_revenue": {
    "2024-01": 29700,
    "2024-02": 33800,
    ...
  }
}
```
# AI-powered-Management-Information-System
