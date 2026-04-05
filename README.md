# 📦 SupplyChain-Env — AI Agent Benchmark Environment

> An OpenEnv-compatible AI benchmark environment simulating **supply chain crisis scenarios**

---

## 🧠 What is this?

SupplyChain-Env is a custom AI agent evaluation environment that simulates real-world supply chain disruptions. AI agents are tested on their ability to identify risks, reallocate inventory, and recover from crises — with a custom reward/scoring system to measure performance.

---

## ✨ Features

- ✅ 3 progressive challenge tasks (risk identification → inventory reallocation → crisis recovery)
- ✅ Custom reward & scoring logic for AI agent evaluation
- ✅ REST API endpoints via FastAPI for agent interaction
- ✅ Docker containerization for reproducible environments
- ✅ Compatible with OpenEnv / OpenAI Gym-style interfaces
- ✅ Pydantic v2 data validation throughout

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| API | FastAPI |
| Validation | Pydantic v2 |
| Containerization | Docker |
| Interface | OpenEnv-compatible REST API |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Docker

### Run locally

```bash
# Clone the repo
git clone https://github.com/sanskritika2409/SupplyChain-Env.git
cd SupplyChain-Env

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload
```

### Run with Docker

```bash
docker build -t supplychain-env .
docker run -p 8000:8000 supplychain-env
```

### API Docs
Once running, visit `http://localhost:8000/docs` for interactive Swagger docs.

---

## 🎯 Tasks

| Task | Description | Difficulty |
|---|---|---|
| Task 1 | Risk Identification | Beginner |
| Task 2 | Inventory Reallocation | Intermediate |
| Task 3 | Crisis Recovery | Advanced |

---

## 👩‍💻 Author

**Sanskritika Awasthi**  
[LinkedIn](https://www.linkedin.com/in/sanskritika-awasthi-9400592a6) | [GitHub](https://github.com/sanskritika2409)
