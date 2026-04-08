import os
import sys
import json
import time
import subprocess
import urllib.request

# ── Auto-install openai if the validator env doesn't have it ──────────────────
try:
    from openai import OpenAI
except ImportError:
    print("[SETUP] openai not found — installing...", flush=True)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai", "-q"])
    from openai import OpenAI
# ─────────────────────────────────────────────────────────────────────────────

# Use API_KEY (validator injected) with fallback to HF_TOKEN
API_KEY = os.getenv("API_KEY") or os.getenv("HF_TOKEN", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")

TASKS = ["risk_identification", "inventory_reallocation", "crisis_recovery"]

SYSTEM_PROMPT = """You are a supply chain crisis manager AI agent.
Respond ONLY with a valid JSON object like this:
{"action_type": "flag_at_risk", "parameters": {"order_ids": ["O1"]}, "reasoning": "brief reason"}
Action types: flag_at_risk, transfer_inventory, expedite_supplier, fulfill_order, cancel_order, advance_day, submit_final
No extra text - JSON only."""

_server_proc = None

def start_server_if_needed():
    global _server_proc
    if "localhost" not in ENV_BASE_URL:
        print("[DEBUG] External ENV_BASE_URL, skipping local server start.", flush=True)
        return

    for _ in range(3):
        try:
            urllib.request.urlopen(ENV_BASE_URL + "/health", timeout=2)
            print("[DEBUG] Server already running.", flush=True)
            return
        except:
            pass

    if not os.path.exists("app.py"):
        print("[DEBUG] app.py not found — assuming validator provides the env.", flush=True)
        return

    print("[DEBUG] Starting local server...", flush=True)
    _server_proc = subprocess.Popen(
        ["python", "app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    for _ in range(30):
        try:
            urllib.request.urlopen(ENV_BASE_URL + "/health", timeout=1)
            print("[DEBUG] Server ready.", flush=True)
            return
        except:
            time.sleep(1)

    print("[WARN] Server did not start in 30s — continuing anyway.", flush=True)

def stop_server():
    global _server_proc
    if _server_proc:
        _server_proc.terminate()
        _server_proc = None

def log_start(task, env, model):
    print("[START] task=" + task + " env=" + env + " model=" + model, flush=True)

def log_step(step, action, reward, done, error=None):
    print("[STEP] step=" + str(step) + " action=" + str(action) +
          " reward=" + str(round(reward, 2)) + " done=" + str(done).lower() +
          " error=" + str(error or "null"), flush=True)

def log_end(success, steps, score, rewards):
    print("[END] success=" + str(success).lower() + " steps=" + str(steps) +
          " score=" + str(round(score, 3)), flush=True)

def get_action(client, observation, step):
    try:
        obs_str = json.dumps(observation, indent=2)
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Step " + str(step) + ". State:\n" + obs_str + "\nWhat is your next action?"}
            ],
            temperature=0.3,
            max_tokens=512,
        )
        text = resp.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        print("[WARN] " + str(e), flush=True)
        return {"action_type": "submit_final", "parameters": {}, "reasoning": "error fallback"}

def run_task(client, task_id):
    log_start(task_id, "supply-chain-env", MODEL_NAME)
    try:
        req = urllib.request.Request(
            ENV_BASE_URL + "/reset?task_id=" + task_id,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            obs = json.loads(r.read())
    except Exception as e:
        print("[ERROR] Could not reset env: " + str(e), flush=True)
        log_end(False, 0, 0.0, [])
        return 0.0

    rewards = []
    final_score = 0.0
    done = False
    max_steps = obs.get("max_steps", 8)

    for step in range(1, max_steps + 1):
        if done:
            break
        action = get_action(client, obs, step)
        action_type = action.get("action_type", "unknown")
        data = json.dumps(action).encode()
        req = urllib.request.Request(
            ENV_BASE_URL + "/step",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                result = json.loads(r.read())
            reward_val = result["reward"]["value"]
            done = result["done"]
            obs = result["observation"]
            if done:
                final_score = reward_val
            rewards.append(reward_val)
            log_step(step, action_type, reward_val, done)
        except Exception as e:
            log_step(step, action_type, 0.0, True, str(e))
            break

    log_end(final_score >= 0.3, len(rewards), final_score, rewards)
    return final_score

def main():
    print("Starting inference...", flush=True)
    print("[DEBUG] API_BASE_URL=" + API_BASE_URL, flush=True)
    print("[DEBUG] API_KEY set=" + str(bool(API_KEY)), flush=True)

    if not API_KEY:
        print("ERROR: Set API_KEY or HF_TOKEN environment variable", flush=True)
        return

    try:
        start_server_if_needed()
        # Always use validator-provided API_BASE_URL and API_KEY
        client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
        scores = []
        for task_id in TASKS:
            score = run_task(client, task_id)
            scores.append(score)
            print("[SUMMARY] task=" + task_id + " score=" + str(round(score, 3)), flush=True)
        avg = sum(scores) / len(scores) if scores else 0.0
        print("[SUMMARY] average_score=" + str(round(avg, 3)), flush=True)
    finally:
        stop_server()

if __name__ == "__main__":
    main()