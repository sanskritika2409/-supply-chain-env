import os
import sys
import json
import time
import subprocess
import urllib.request

<<<<<<< HEAD
# ── Auto-install openai if the validator env doesn't have it ──────────────────
try:
    from openai import OpenAI
except ImportError:
    print("[SETUP] openai not found — installing...", flush=True)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai", "-q"])
    from openai import OpenAI
# ─────────────────────────────────────────────────────────────────────────────

# Use API_KEY (validator injected) with fallback to HF_TOKEN
API_KEY = os.environ["API_KEY"]
API_BASE_URL = os.environ["API_BASE_URL"]

MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
=======
# MUST use the injected variables exactly like this
API_BASE_URL = os.environ["API_BASE_URL"]
API_KEY = os.environ["API_KEY"]

MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")
>>>>>>> ebc1969 (fix: correct OpenEnv port 7860)

TASKS = ["risk_identification", "inventory_reallocation", "crisis_recovery"]

SYSTEM_PROMPT = """You are a supply chain crisis manager AI agent.
Respond ONLY with a valid JSON object like this:
{"action_type": "flag_at_risk", "parameters": {"order_ids": ["O1"]}, "reasoning": "brief reason"}
Action types: flag_at_risk, transfer_inventory, expedite_supplier, fulfill_order, cancel_order, advance_day, submit_final
No extra text - JSON only.
"""

_server_proc = None


def start_server_if_needed():
    global _server_proc

    if "localhost" not in ENV_BASE_URL:
<<<<<<< HEAD
        print("[DEBUG] External ENV_BASE_URL, skipping local server start.", flush=True)
=======
>>>>>>> ebc1969 (fix: correct OpenEnv port 7860)
        return

    for _ in range(3):
        try:
            urllib.request.urlopen(ENV_BASE_URL + "/health", timeout=2)
<<<<<<< HEAD
            print("[DEBUG] Server already running.", flush=True)
=======
>>>>>>> ebc1969 (fix: correct OpenEnv port 7860)
            return
        except:
            pass

<<<<<<< HEAD
    if not os.path.exists("app.py"):
        print("[DEBUG] app.py not found — assuming validator provides the env.", flush=True)
        return

    print("[DEBUG] Starting local server...", flush=True)
=======
>>>>>>> ebc1969 (fix: correct OpenEnv port 7860)
    _server_proc = subprocess.Popen(
        ["python", "app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(30):
        try:
            urllib.request.urlopen(ENV_BASE_URL + "/health", timeout=1)
            return
        except:
            time.sleep(1)

<<<<<<< HEAD
    print("[WARN] Server did not start in 30s — continuing anyway.", flush=True)
=======
    raise RuntimeError("Server failed to start")

>>>>>>> ebc1969 (fix: correct OpenEnv port 7860)

def stop_server():
    global _server_proc
    if _server_proc:
        _server_proc.terminate()
        _server_proc = None

<<<<<<< HEAD
def log_start(task, env, model):
    print("[START] task=" + task + " env=" + env + " model=" + model, flush=True)

def log_step(step, action, reward, done, error=None):
    print("[STEP] step=" + str(step) + " action=" + str(action) +
          " reward=" + str(round(reward, 2)) + " done=" + str(done).lower() +
          " error=" + str(error or "null"), flush=True)

def log_end(success, steps, score, rewards):
    print("[END] success=" + str(success).lower() + " steps=" + str(steps) +
          " score=" + str(round(score, 2)) +
          " rewards=" + ",".join(str(round(r, 2)) for r in rewards), flush=True)
=======
>>>>>>> ebc1969 (fix: correct OpenEnv port 7860)

def get_action(client, observation, step):
    obs_str = json.dumps(observation)

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Step {step}. State:\n{obs_str}\nWhat is your next action?"}
        ],
        temperature=0.3,
        max_tokens=200,
    )

    text = resp.choices[0].message.content.strip()

    try:
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        return json.loads(text.strip())

    except:
        return {
            "action_type": "submit_final",
            "parameters": {},
            "reasoning": "fallback"
        }


def run_task(client, task_id):
<<<<<<< HEAD
    log_start(task_id, "supply-chain-env", MODEL_NAME)
=======
>>>>>>> ebc1969 (fix: correct OpenEnv port 7860)
    try:
        req = urllib.request.Request(
            ENV_BASE_URL + "/reset?task_id=" + task_id,
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=30) as r:
            obs = json.loads(r.read())

    except:
        return 0.0

    final_score = 0.0
    done = False
    max_steps = obs.get("max_steps", 8)

    for step in range(1, max_steps + 1):

        if done:
            break

        action = get_action(client, obs, step)

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

            done = result["done"]
            obs = result["observation"]

            if done:
                final_score = result["reward"]["value"]

        except:
            break

    return final_score


def main():
    print("Starting inference...", flush=True)
    print("[DEBUG] API_BASE_URL=" + API_BASE_URL, flush=True)
    print("[DEBUG] API_KEY set=" + str(bool(API_KEY)), flush=True)

<<<<<<< HEAD
    if not API_KEY:
        print("ERROR: Set API_KEY or HF_TOKEN environment variable", flush=True)
        return

    try:
        start_server_if_needed()
        # Always use validator-provided API_BASE_URL and API_KEY
        client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
=======
    client = OpenAI(
        base_url=os.environ["API_BASE_URL"],
        api_key=os.environ["API_KEY"]
    )

    try:
        start_server_if_needed()

>>>>>>> ebc1969 (fix: correct OpenEnv port 7860)
        scores = []

        for task_id in TASKS:
            score = run_task(client, task_id)
            scores.append(score)
<<<<<<< HEAD
            print("[SUMMARY] task=" + task_id + " score=" + str(round(score, 2)), flush=True)
        avg = sum(scores) / len(scores) if scores else 0.0
        print("[SUMMARY] average_score=" + str(round(avg, 3)), flush=True)
=======

        print("Average score:", sum(scores) / len(scores), flush=True)

>>>>>>> ebc1969 (fix: correct OpenEnv port 7860)
    finally:
        stop_server()


if __name__ == "__main__":
    main()