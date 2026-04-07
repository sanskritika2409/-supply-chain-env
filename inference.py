import os
import json
import time
import urllib.request
import urllib.error
from openai import OpenAI

HF_TOKEN = os.getenv("HF_TOKEN", "")
API_BASE_URL = "https://router.huggingface.co/v1"
MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")

TASKS = ["risk_identification", "inventory_reallocation", "crisis_recovery"]

SYSTEM_PROMPT = """You are a supply chain crisis manager AI agent.
Respond ONLY with a valid JSON object like this:
{"action_type": "flag_at_risk", "parameters": {"order_ids": ["O1"]}, "reasoning": "brief reason"}
Action types: flag_at_risk, transfer_inventory, expedite_supplier, fulfill_order, cancel_order, advance_day, submit_final
No extra text - JSON only."""


def log_start(task, model):
    print("[START] task=" + task + " model=" + model, flush=True)


def log_step(step, action, reward, done, error=None):
    print("[STEP] step=" + str(step) + " action=" + action +
          " reward=" + str(round(reward, 2)) + " done=" + str(done).lower() +
          " error=" + str(error or "null"), flush=True)


def log_end(success, steps, score, rewards):
    print("[END] success=" + str(success).lower() + " steps=" + str(steps) +
          " score=" + str(round(score, 3)), flush=True)


def wait_for_server(base_url, retries=20, delay=3):
    for i in range(retries):
        try:
            with urllib.request.urlopen(base_url + "/health", timeout=5) as r:
                if r.status == 200:
                    print("[INFO] Server is ready.", flush=True)
                    return True
        except Exception as e:
            print(f"[INFO] Waiting for server... attempt {i+1}/{retries}: {e}", flush=True)
            time.sleep(delay)
    print("[ERROR] Server did not become ready in time.", flush=True)
    return False


def http_post(url, data=None, timeout=30):
    try:
        payload = json.dumps(data).encode() if data is not None else b""
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"[WARN] HTTP {e.code} on POST {url}: {e.reason}", flush=True)
        return None
    except urllib.error.URLError as e:
        print(f"[WARN] URLError on POST {url}: {e.reason}", flush=True)
        return None
    except json.JSONDecodeError as e:
        print(f"[WARN] JSON decode error: {e}", flush=True)
        return None
    except Exception as e:
        print(f"[WARN] Unexpected error on POST {url}: {e}", flush=True)
        return None


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
        print("[WARN] get_action error: " + str(e), flush=True)
        return {"action_type": "submit_final", "parameters": {}, "reasoning": "error fallback"}


def run_task(client, task_id):
    log_start(task_id, MODEL_NAME)

    obs = http_post(ENV_BASE_URL + "/reset?task_id=" + task_id)
    if obs is None:
        print(f"[ERROR] Failed to reset task {task_id}, skipping.", flush=True)
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

        result = http_post(ENV_BASE_URL + "/step", data=action)
        if result is None:
            log_step(step, action_type, 0.0, True, "step request failed")
            break

        try:
            reward_val = result["reward"]["value"]
            done = result["done"]
            obs = result["observation"]
            if done:
                final_score = reward_val
            rewards.append(reward_val)
            log_step(step, action_type, reward_val, done)
        except (KeyError, TypeError) as e:
            log_step(step, action_type, 0.0, True, str(e))
            break

    log_end(final_score >= 0.3, len(rewards), final_score, rewards)
    return final_score


def main():
    print("Starting inference...", flush=True)

    if not HF_TOKEN:
        print("ERROR: Set HF_TOKEN environment variable", flush=True)
        return

    if not wait_for_server(ENV_BASE_URL):
        print("ERROR: Cannot reach environment server. Exiting.", flush=True)
        return

    try:
        client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    except Exception as e:
        print(f"ERROR: Failed to initialize OpenAI client: {e}", flush=True)
        return

    scores = []
    for task_id in TASKS:
        try:
            score = run_task(client, task_id)
        except Exception as e:
            print(f"[ERROR] Unhandled error in task {task_id}: {e}", flush=True)
            score = 0.0
        scores.append(score)
        print("[SUMMARY] task=" + task_id + " score=" + str(round(score, 3)), flush=True)

    if scores:
        print("[SUMMARY] average_score=" + str(round(sum(scores) / len(scores), 3)), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] Unhandled exception: {e}", flush=True)
