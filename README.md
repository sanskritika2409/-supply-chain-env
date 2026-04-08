# 🏭 SupplyChain-Env

**An OpenEnv environment for AI supply chain crisis management**

## Why This Matters
Supply chain disruptions cost the global economy $4 trillion in 2021 alone (COVID). 
This environment trains AI agents to respond to real crises: supplier failures, 
warehouse damage, and transport delays — under budget and time pressure.

## Tasks

| Task | Difficulty | Description | Baseline Score |
|------|-----------|-------------|----------------|
| `risk_identification` | Easy | Identify at-risk orders after supplier fire | ~0.75 |
| `inventory_reallocation` | Medium | Reallocate inventory before warehouse floods | ~0.45 |
| `crisis_recovery` | Hard | 7-day multi-disruption crisis management | ~0.25 |

## Action Space
| Action | Parameters | Description |
|--------|-----------|-------------|
| `flag_at_risk` | `order_ids: list` | Mark orders as at-risk |
| `transfer_inventory` | `from_warehouse_id, to_warehouse_id, product, quantity` | Move stock |
| `expedite_supplier` | `supplier_id` | Pay $2000 to reactivate supplier |
| `fulfill_order` | `order_id` | Ship an order if inventory available |
| `cancel_order` | `order_id` | Cancel (penalty for high priority) |
| `advance_day` | — | Move to next day (crisis_recovery only) |
| `submit_final` | — | End episode and compute final score |

## Observation Space
```json
{
  "day": 1,
  "budget": 80000.0,
  "suppliers": [...],
  "warehouses": [...],
  "orders": [...],
  "disruptions": [...],
  "task_description": "..."
}
```

## Setup
```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

## Run Baseline
```bash
export HF_TOKEN=your_token
export ENV_BASE_URL=http://localhost:8000
python inference.py
```

## Docker
```bash
docker build -t supply-chain-env .
docker run -p 7860:7860 supply-chain-env
```