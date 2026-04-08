import os
import json
import urllib.request
from typing import List, Optional
from openai import OpenAI

# ── Config ──────────────────────────────────────────────────────────────────
HF_TOKEN = "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"
API_BASE_URL = "https://router.huggingface.co/v1"
MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")
TASKS = ["risk_identification", "inventory_reallocation", "crisis_recovery"]

SYSTEM_PROMPT = """You are a supply chain crisis manager AI agent.
Respond ONLY with a valid JSON object like this:
{"action_type": "flag_at_risk", "parameters": {"order_ids": ["O1"]}, "reasoning": "brief reason"}

Action types: flag_at_risk, transfer_inventory, expedite_supplier, fulfill_order, cancel_order, advance_day, submit_final
Read task_description carefully. No extra text — JSON only."""


def log_start(task, model):
    print(f"[START] task={task} model={model}", flush=True)

def log_step(step, action, reward, done, error=None):
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error or 'null'}", flush=True)

def log_end(success, steps, score, rewards):
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={','.join(f'{r:.2f}' for r in rewards)}", flush=True)


def get_action(client, observation, step):
    try:
        obs_str = json.dumps(observation, indent=2)
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Step {step}. State:\n{obs_str}\nWhat is your next action?"}
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
        print(f"  [WARN] get_action error: {e}", flush=True)
        return {"action_type": "submit_final", "parameters": {}, "reasoning": "error fallback"}


def run_task(client, task_id):
    log_start(task_id, MODEL_NAME)

    # Reset
    req = urllib.request.Request(
        f"{ENV_BASE_URL}/reset?task_id={task_id}",
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        obs = json.loads(r.read())

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
            f"{ENV_BASE_URL}/step",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as r:
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
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    scores = []
    for task_id in TASKS:
        score = run_task(client, task_id)
        scores.append(score)
        print(f"[SUMMARY] task={task_id} score={score:.3f}", flush=True)
    print(f"[SUMMARY] average_score={sum(scores)/len(scores):.3f}", flush=True)


if __name__ == "__main__":
    main()