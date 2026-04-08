from fastapi import FastAPI, HTTPException
import os

from models import Action, Observation, Reward, StepResult, StateResult
from environment import SupplyChainEnv, TASKS

app = FastAPI(
    title="SupplyChain-Env",
    description="OpenEnv supply chain crisis management",
    version="1.0.0",
)

_env = SupplyChainEnv("risk_identification")

@app.get("/")
def root():
    return {"name": "SupplyChain-Env", "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks")
def list_tasks():
    return {"tasks": list(TASKS.keys())}

@app.post("/reset")
def reset(task_id: str = "risk_identification"):
    global _env
    if task_id not in TASKS:
        raise HTTPException(status_code=400, detail=f"Unknown task: {task_id}")
    _env = SupplyChainEnv(task_id)
    obs = _env.reset()
    return obs.model_dump()

@app.post("/step")
def step(action: Action):
    result = _env.step(action)
    return result.model_dump()

@app.get("/state")
def state():
    return _env.state()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)