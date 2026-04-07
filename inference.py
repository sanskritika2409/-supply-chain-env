import os
import json
import time
import urllib.request
import urllib.error
from openai import OpenAI

HF_TOKEN     = os.getenv("HF_TOKEN", "")
API_BASE_URL = "https://router.huggingface.co/v1"
MODEL_NAME   = "Qwen/Qwen2.5-72B-Instruct"
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")

TASKS = ["risk_identification", "inventory_reallocation", "crisis_recovery"]

SYSTEM_PROMPT = """You are a supply chain crisis manager AI agent.
Respond ONLY with a valid JSON object like this:
{"action_type": "flag_at_risk", "parameters": {"order_ids": ["O1"]}, "reasoning": "brief reason"}
Action types: flag_at_risk, transfer_inventory, expedite_supplier, fulfill_order, cancel_order, advance_day, submit_final
No extra text - JSON only."""


# ── Logging helpers ──────────────────────────────────────────────────────────

def log_start(task, model):
    print(f"[START] task={task} model={model}", flush=True)

def log_step(step, action, reward, done, error=None):
    print(f"[STEP] step={step} action={action} reward={round(reward,2)} "
          f"done={str(done).lower()} error={error or 'null'}", flush=True)

def log_end(success, steps, score, rewards):
    print(f"[END] success={str(success).lower()} steps={steps} "
          f"score={round(score,3)}", flush=True)


# ── Network helpers ──────────────────────────────────────────────────────────

def env_post(path, payload=None, timeout=30):
    """POST to env server; returns parsed JSON or raises on failure."""
    data = json.dumps(payload).encode() if payload is not None else b""
    req = urllib.request.Request(
        ENV_BASE_URL + path,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def wait_for_server(retries=15, delay=3):
    """Poll /health until the env server responds."""
    print(f"[INFO] Waiting for env server at {ENV_BASE_URL} ...", flush=True)
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(ENV_BASE_URL + "/health", method="GET")
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status == 200:
                    print("[INFO] Env server ready.", flush=True)
                    return True
        except Exception as e:
            print(f"[INFO] Attempt {attempt}/{retries} - not ready yet: {e}", flush=True)
        time.sleep(delay)
    print("[ERROR] Env server never became ready.", flush=True)
    return False


# ── LLM action selection ─────────────────────────────────────────────────────

def get_action(client, observation, step):
    try:
        obs_str = json.dumps(observation, indent=2)
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",
                 "content": f"Step {step}. State:\n{obs_str}\nWhat is your next action?"}
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
        print(f"[WARN] get_action failed: {e}", flush=True)
        return {"action_type": "submit_final", "parameters": {}, "reasoning": "error fallback"}


# ── Task runner ──────────────────────────────────────────────────────────────

def run_task(client, task_id):
    log_start(task_id, MODEL_NAME)

    try:
        obs = env_post(f"/reset?task_id={task_id}")
    except Exception as e:
        print(f"[ERROR] /reset failed for task '{task_id}': {e}", flush=True)
        log_end(False, 0, 0.0, [])
        return 0.0

    rewards     = []
    final_score = 0.0
    done        = False
    max_steps   = obs.get("max_steps", 8)

    for step in range(1, max_steps + 1):
        if done:
            break

        action      = get_action(client, obs, step)
        action_type = action.get("action_type", "unknown")

        try:
            result     = env_post("/step", action)
            reward_val = result["reward"]["value"]
            done       = result["done"]
            obs        = result["observation"]
            if done:
                final_score = reward_val
            rewards.append(reward_val)
            log_step(step, action_type, reward_val, done)
        except Exception as e:
            print(f"[ERROR] /step failed at step {step}: {e}", flush=True)
            log_step(step, action_type, 0.0, True, str(e))
            break

    log_end(final_score >= 0.3, len(rewards), final_score, rewards)
    return final_score


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    print("Starting inference...", flush=True)

    if not HF_TOKEN:
        print("[ERROR] HF_TOKEN environment variable is not set.", flush=True)
        return  # exit 0 — not a code crash

    if not wait_for_server(retries=15, delay=3):
        print("[ERROR] Aborting: env server unreachable.", flush=True)
        return  # exit 0

    try:
        client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    except Exception as e:
        print(f"[ERROR] Could not create LLM client: {e}", flush=True)
        return

    scores = []
    for task_id in TASKS:
        try:
            score = run_task(client, task_id)
        except Exception as e:
            print(f"[ERROR] Unexpected crash in run_task({task_id}): {e}", flush=True)
            score = 0.0
        scores.append(score)
        print(f"[SUMMARY] task={task_id} score={round(score, 3)}", flush=True)

    avg = sum(scores) / len(scores) if scores else 0.0
    print(f"[SUMMARY] average_score={round(avg, 3)}", flush=True)
    # Script always exits with code 0 — no sys.exit(1) anywhere


if __name__ == "__main__":
    main()
