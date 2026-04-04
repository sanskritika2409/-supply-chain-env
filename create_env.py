content = '''import copy
from typing import Any, Dict, Tuple
from models import (
    Action, Disruption, Observation, Order, Priority,
    Reward, StepResult, Supplier, Warehouse
)

TASK_EASY = {
    "task_id": "risk_identification",
    "task_description": "TASK Easy: Factory fire at GlobalParts! Find all at-risk orders. Use flag_at_risk then submit_final. Score = F1. Max steps: 8.",
    "max_steps": 8,
    "disruptions": [
        Disruption(id="D1", disruption_type="supplier_failure", description="Factory fire at GlobalParts Inc.", affected_entity_id="S1", severity=0.9, day_started=1)
    ],
    "suppliers": [
        Supplier(id="S1", name="GlobalParts Inc", products=["widget_A","widget_B"], reliability=0.95, is_active=False, stock={"widget_A":0,"widget_B":0}),
        Supplier(id="S2", name="ReliaCo", products=["widget_C","gadget_X"], reliability=0.85, is_active=True, stock={"widget_C":500,"gadget_X":200}),
    ],
    "warehouses": [
        Warehouse(id="W1", name="East Hub", location="New York", capacity=1000, inventory={"widget_A":50,"widget_C":200}),
        Warehouse(id="W2", name="West Hub", location="Los Angeles", capacity=1000, inventory={"widget_B":30,"gadget_X":100}),
    ],
    "orders": [
        Order(id="O1", customer="MegaStore", product="widget_A", quantity=40, deadline_day=3, priority=Priority.CRITICAL, supplier_id="S1", warehouse_id="W1"),
        Order(id="O2", customer="QuickShop", product="widget_C", quantity=100, deadline_day=4, priority=Priority.HIGH, supplier_id="S2", warehouse_id="W1"),
        Order(id="O3", customer="TechCorp", product="widget_B", quantity=25, deadline_day=2, priority=Priority.CRITICAL, supplier_id="S1", warehouse_id="W2"),
        Order(id="O4", customer="LocalMart", product="gadget_X", quantity=50, deadline_day=5, priority=Priority.MEDIUM, supplier_id="S2", warehouse_id="W2"),
        Order(id="O5", customer="BigBox", product="widget_A", quantity=10, deadline_day=6, priority=Priority.LOW, supplier_id="S1", warehouse_id="W1"),
    ],
    "budget": 100000.0,
    "at_risk_order_ids": {"O1", "O3", "O5"},
}

TASK_MEDIUM = {
    "task_id": "inventory_reallocation",
    "task_description": "TASK Medium: West Hub flooding! Transfer inventory to East Hub. Budget 50000. Transfer costs 500 each. Max steps: 12.",
    "max_steps": 12,
    "disruptions": [
        Disruption(id="D2", disruption_type="warehouse_damage", description="West Hub flooding.", affected_entity_id="W2", severity=0.8, day_started=1)
    ],
    "suppliers": [
        Supplier(id="S1", name="GlobalParts Inc", products=["widget_A","widget_B"], reliability=0.9, is_active=True, stock={"widget_A":300,"widget_B":200}),
        Supplier(id="S2", name="ReliaCo", products=["widget_C"], reliability=0.85, is_active=True, stock={"widget_C":400}),
    ],
    "warehouses": [
        Warehouse(id="W1", name="East Hub", location="New York", capacity=2000, inventory={"widget_A":100,"widget_C":150}),
        Warehouse(id="W2", name="West Hub", location="Los Angeles", capacity=1000, inventory={"widget_B":200,"widget_A":80}),
    ],
    "orders": [
        Order(id="O1", customer="HospitalNet", product="widget_B", quantity=150, deadline_day=3, priority=Priority.CRITICAL, supplier_id="S1", warehouse_id="W2"),
        Order(id="O2", customer="CityGov", product="widget_A", quantity=60, deadline_day=3, priority=Priority.CRITICAL, supplier_id="S1", warehouse_id="W2"),
        Order(id="O3", customer="SchoolBoard", product="widget_C", quantity=100, deadline_day=4, priority=Priority.HIGH, supplier_id="S2", warehouse_id="W1"),
        Order(id="O4", customer="Boutique", product="widget_A", quantity=20, deadline_day=5, priority=Priority.MEDIUM, supplier_id="S1", warehouse_id="W1"),
        Order(id="O5", customer="Startup", product="widget_B", quantity=30, deadline_day=6, priority=Priority.LOW, supplier_id="S1", warehouse_id="W2"),
    ],
    "budget": 50000.0,
    "priority_weights": {Priority.CRITICAL:1.0, Priority.HIGH:0.6, Priority.MEDIUM:0.3, Priority.LOW:0.1},
}

TASK_HARD = {
    "task_id": "crisis_recovery",
    "task_description": "TASK Hard: 3 disruptions at once! 7 days, 80000 budget. Advance days, transfer, expedite, fulfill. Score = 0.5*fulfillment + 0.3*cost + 0.2*speed. Max steps: 20.",
    "max_steps": 20,
    "disruptions": [
        Disruption(id="D1", disruption_type="supplier_failure", description="PrimeParts bankrupt.", affected_entity_id="S3", severity=0.7, day_started=1),
        Disruption(id="D2", disruption_type="warehouse_damage", description="South Hub storm.", affected_entity_id="W3", severity=0.5, day_started=1),
        Disruption(id="D3", disruption_type="transport_delay", description="Port strike.", affected_entity_id="W1", severity=0.4, day_started=1),
    ],
    "suppliers": [
        Supplier(id="S1", name="GlobalParts Inc", products=["comp_A"], reliability=0.9, is_active=True, stock={"comp_A":500}),
        Supplier(id="S2", name="ReliaCo", products=["comp_B"], reliability=0.85, is_active=True, stock={"comp_B":300}),
        Supplier(id="S3", name="PrimeParts", products=["comp_C","comp_D"], reliability=0.3, is_active=False, stock={"comp_C":0,"comp_D":0}),
    ],
    "warehouses": [
        Warehouse(id="W1", name="East Hub", location="New York", capacity=2000, inventory={"comp_A":200,"comp_B":100}),
        Warehouse(id="W2", name="West Hub", location="Los Angeles", capacity=1500, inventory={"comp_A":50,"comp_C":80}),
        Warehouse(id="W3", name="South Hub", location="Miami", capacity=500, inventory={"comp_D":60,"comp_B":40}),
    ],
    "orders": [
        Order(id="O1", customer="AeroSpace Co", product="comp_A", quantity=150, deadline_day=3, priority=Priority.CRITICAL, supplier_id="S1", warehouse_id="W1"),
        Order(id="O2", customer="MedDevices", product="comp_B", quantity=80, deadline_day=4, priority=Priority.CRITICAL, supplier_id="S2", warehouse_id="W3"),
        Order(id="O3", customer="AutoMaker", product="comp_C", quantity=60, deadline_day=5, priority=Priority.HIGH, supplier_id="S3", warehouse_id="W2"),
        Order(id="O4", customer="Electronics", product="comp_D", quantity=40, deadline_day=5, priority=Priority.HIGH, supplier_id="S3", warehouse_id="W3"),
        Order(id="O5", customer="RetailChain", product="comp_A", quantity=100, deadline_day=6, priority=Priority.MEDIUM, supplier_id="S1", warehouse_id="W2"),
        Order(id="O6", customer="SmallBiz", product="comp_B", quantity=30, deadline_day=7, priority=Priority.LOW, supplier_id="S2", warehouse_id="W1"),
    ],
    "budget": 80000.0,
    "max_days": 7,
}

TASKS = {
    "risk_identification": TASK_EASY,
    "inventory_reallocation": TASK_MEDIUM,
    "crisis_recovery": TASK_HARD,
}


class SupplyChainEnv:

    def __init__(self, task_id="risk_identification"):
        if task_id not in TASKS:
            raise ValueError(f"Unknown task: {task_id}")
        self.task_id = task_id
        self._template = TASKS[task_id]
        self._state = {}
        self.reset()

    def reset(self):
        t = self._template
        self._state = {
            "task_id": t["task_id"],
            "task_description": t["task_description"],
            "day": 1,
            "budget": t["budget"],
            "max_budget": t["budget"],
            "max_steps": t["max_steps"],
            "steps_taken": 0,
            "total_reward": 0.0,
            "is_done": False,
            "flagged_order_ids": set(),
            "suppliers": copy.deepcopy(t["suppliers"]),
            "warehouses": copy.deepcopy(t["warehouses"]),
            "orders": copy.deepcopy(t["orders"]),
            "disruptions": copy.deepcopy(t["disruptions"]),
            "fulfilled_orders": set(),
            "cancelled_orders": set(),
            "expedited_suppliers": set(),
        }
        return self._build_observation("Welcome! Read the task description carefully.")

    def step(self, action):
        if self._state["is_done"]:
            obs = self._build_observation("Episode done. Call reset().")
            return StepResult(observation=obs, reward=Reward(value=0.0, message="Done"), done=True)
        self._state["steps_taken"] += 1
        reward, message = self._apply_action(action)
        done = (
            self._state["is_done"]
            or self._state["steps_taken"] >= self._state["max_steps"]
            or action.action_type == "submit_final"
        )
        if done:
            self._state["is_done"] = True
            final_reward = self._compute_final_score()
            reward = final_reward
            message = f"Episode complete. Final score: {final_reward.value:.3f}"
        self._state["total_reward"] += reward.value
        obs = self._build_observation(message)
        return StepResult(observation=obs, reward=reward, done=done,
                          info={"steps_taken": self._state["steps_taken"], "budget_remaining": self._state["budget"]})

    def state(self):
        return {
            "task_id": self._state["task_id"],
            "day": self._state["day"],
            "budget": self._state["budget"],
            "steps_taken": self._state["steps_taken"],
            "total_reward": self._state["total_reward"],
            "orders_fulfilled": len(self._state["fulfilled_orders"]),
            "orders_at_risk": sum(1 for o in self._state["orders"] if o.is_flagged_at_risk),
            "active_disruptions": len(self._state["disruptions"]),
            "is_done": self._state["is_done"],
        }

    def _apply_action(self, action):
        at = action.action_type
        p = action.parameters
        if at == "flag_at_risk": return self._action_flag_at_risk(p)
        elif at == "transfer_inventory": return self._action_transfer(p)
        elif at == "expedite_supplier": return self._action_expedite(p)
        elif at == "fulfill_order": return self._action_fulfill(p)
        elif at == "cancel_order": return self._action_cancel(p)
        elif at == "advance_day": return self._action_advance_day()
        elif at == "submit_final": return Reward(value=0.0, message="Submitting..."), "Finalizing..."
        else: return Reward(value=0.0, message=f"Unknown: {at}"), f"Unknown: {at}"

    def _action_flag_at_risk(self, p):
        order_ids = p.get("order_ids", [])
        if isinstance(order_ids, str): order_ids = [order_ids]
        flagged = set(order_ids)
        self._state["flagged_order_ids"].update(flagged)
        for o in self._state["orders"]:
            if o.id in flagged: o.is_flagged_at_risk = True
        if self.task_id == "risk_identification":
            ground_truth = self._template.get("at_risk_order_ids", set())
            correct = self._state["flagged_order_ids"] & ground_truth
            fp = self._state["flagged_order_ids"] - ground_truth
            precision = len(correct) / max(len(self._state["flagged_order_ids"]), 1)
            recall = len(correct) / max(len(ground_truth), 1)
            partial = 0.5 * (precision + recall) * 0.3
            return Reward(value=min(partial, 0.3), components={"precision": precision, "recall": recall}, message=f"Flagged {len(flagged)} orders."), f"Flagged: {list(flagged)}"
        return Reward(value=0.05, message="Orders flagged."), f"Flagged: {list(flagged)}"

    def _action_transfer(self, p):
        cost = 500.0
        if self._state["budget"] < cost: return Reward(value=0.0, message="No budget"), "No budget."
        from_id = p.get("from_warehouse_id", "")
        to_id = p.get("to_warehouse_id", "")
        product = p.get("product", "")
        qty = int(p.get("quantity", 0))
        src = next((w for w in self._state["warehouses"] if w.id == from_id), None)
        dst = next((w for w in self._state["warehouses"] if w.id == to_id), None)
        if not src or not dst: return Reward(value=0.0, message="Invalid warehouses"), "Invalid warehouses."
        available = src.inventory.get(product, 0)
        qty = min(qty, available)
        if qty <= 0: return Reward(value=0.0, message="Nothing to transfer"), "Nothing to transfer."
        src.inventory[product] = available - qty
        dst.inventory[product] = dst.inventory.get(product, 0) + qty
        self._state["budget"] -= cost
        return Reward(value=min(qty/100, 1.0)*0.1, message=f"Transferred {qty}"), f"Moved {qty} {product}. Cost: $500"

    def _action_expedite(self, p):
        cost = 2000.0
        supplier_id = p.get("supplier_id", "")
        if self._state["budget"] < cost: return Reward(value=0.0, message="No budget"), "No budget."
        sup = next((s for s in self._state["suppliers"] if s.id == supplier_id), None)
        if not sup: return Reward(value=0.0, message="Not found"), f"No supplier: {supplier_id}"
        if supplier_id in self._state["expedited_suppliers"]: return Reward(value=0.0, message="Already done"), "Already expedited."
        sup.is_active = True
        sup.reliability = min(sup.reliability + 0.2, 1.0)
        for product in sup.products: sup.stock[product] = sup.stock.get(product, 0) + 200
        self._state["budget"] -= cost
        self._state["expedited_suppliers"].add(supplier_id)
        return Reward(value=0.15, message="Expedited!"), f"Expedited {sup.name}. Cost: $2000"

    def _action_fulfill(self, p):
        order_id = p.get("order_id", "")
        order = next((o for o in self._state["orders"] if o.id == order_id), None)
        if not order: return Reward(value=0.0, message="Not found"), f"No order: {order_id}"
        if order.is_fulfilled or order.id in self._state["fulfilled_orders"]: return Reward(value=0.0, message="Already done"), "Already fulfilled."
        if order.id in self._state["cancelled_orders"]: return Reward(value=0.0, message="Cancelled"), "Order cancelled."
        wh = next((w for w in self._state["warehouses"] if w.id == order.warehouse_id), None)
        if not wh or not wh.is_operational: return Reward(value=0.0, message="Warehouse offline"), "Warehouse offline."
        if wh.inventory.get(order.product, 0) < order.quantity:
            return Reward(value=0.05, message="Not enough stock"), f"Need {order.quantity}, have {wh.inventory.get(order.product,0)}."
        wh.inventory[order.product] -= order.quantity
        order.is_fulfilled = True
        self._state["fulfilled_orders"].add(order_id)
        bonus = {Priority.CRITICAL:0.25, Priority.HIGH:0.15, Priority.MEDIUM:0.08, Priority.LOW:0.03}[order.priority]
        day_bonus = max(0, (order.deadline_day - self._state["day"]) * 0.01)
        return Reward(value=min(bonus+day_bonus, 0.3), message=f"Fulfilled {order_id}!"), f"Fulfilled {order_id} for {order.customer}"

    def _action_cancel(self, p):
        order_id = p.get("order_id", "")
        order = next((o for o in self._state["orders"] if o.id == order_id), None)
        if not order or order.is_fulfilled: return Reward(value=0.0, message="Cannot cancel"), "Cannot cancel."
        self._state["cancelled_orders"].add(order_id)
        return Reward(value=0.0, message=f"Cancelled {order_id}"), f"Cancelled {order_id}"

    def _action_advance_day(self):
        if self.task_id != "crisis_recovery": return Reward(value=0.0, message="Not valid"), "Only for crisis_recovery."
        max_days = self._template.get("max_days", 7)
        if self._state["day"] >= max_days:
            self._state["is_done"] = True
            return Reward(value=0.0, message="Max days"), "All days done."
        self._state["day"] += 1
        penalty = sum(0.05 for o in self._state["orders"]
                      if o.deadline_day < self._state["day"] and not o.is_fulfilled
                      and o.id not in self._state["cancelled_orders"] and o.priority == Priority.CRITICAL)
        return Reward(value=max(-penalty, -0.2), message=f"Day {self._state[\'day\']}"), f"Day {self._state[\'day\']} begins."

    def _compute_final_score(self):
        if self.task_id == "risk_identification": return self._score_easy()
        elif self.task_id == "inventory_reallocation": return self._score_medium()
        else: return self._score_hard()

    def _score_easy(self):
        ground_truth = self._template.get("at_risk_order_ids", set())
        flagged = self._state["flagged_order_ids"]
        tp = len(flagged & ground_truth)
        fp = len(flagged - ground_truth)
        fn = len(ground_truth - flagged)
        precision = tp / max(tp+fp, 1)
        recall = tp / max(tp+fn, 1)
        f1 = 2*precision*recall / max(precision+recall, 1e-6)
        return Reward(value=round(f1,4), components={"f1":f1}, message=f"F1={f1:.3f}")

    def _score_medium(self):
        weights = self._template.get("priority_weights", {})
        total_w, earned_w = 0.0, 0.0
        for o in self._state["orders"]:
            w = weights.get(o.priority, 0.0)
            total_w += w
            if o.id in self._state["fulfilled_orders"]: earned_w += w
        fulfillment = earned_w / max(total_w, 1e-6)
        cost_used = self._template["budget"] - self._state["budget"]
        cost_eff = 1.0 - (cost_used / max(self._template["budget"], 1))
        score = 0.7*fulfillment + 0.3*cost_eff
        return Reward(value=round(min(score,1.0),4), components={"fulfillment":fulfillment,"cost_eff":cost_eff}, message=f"Fill={fulfillment:.3f}")

    def _score_hard(self):
        total = len(self._state["orders"])
        fulfilled = len(self._state["fulfilled_orders"])
        fill_rate = fulfilled / max(total, 1)
        cost_used = self._template["budget"] - self._state["budget"]
        cost_eff = 1.0 - min(cost_used/self._template["budget"], 1.0)
        speed = sum(1.0/max(total,1) for o in self._state["orders"]
                    if o.id in self._state["fulfilled_orders"] and o.deadline_day >= self._state["day"])
        score = 0.5*fill_rate + 0.3*cost_eff + 0.2*speed
        return Reward(value=round(min(score,1.0),4), components={"fill":fill_rate,"cost":cost_eff,"speed":speed}, message=f"Fill={fill_rate:.2f}")

    def _build_observation(self, message):
        s = self._state
        return Observation(
            day=s["day"], budget=s["budget"], max_budget=s["max_budget"],
            suppliers=s["suppliers"], warehouses=s["warehouses"],
            orders=s["orders"], disruptions=s["disruptions"],
            message=message, task_id=s["task_id"],
            task_description=s["task_description"],
            steps_taken=s["steps_taken"], max_steps=s["max_steps"],
        )
'''

with open("environment.py", "w") as f:
    f.write(content)
print("environment.py created!")