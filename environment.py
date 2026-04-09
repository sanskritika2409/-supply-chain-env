import copy
import random
from typing import Any, Dict, Optional, Tuple

from models import (
    Action, Disruption, Observation, Order, Priority,
    Reward, StepResult, Supplier, Warehouse
)


# ── Scenario templates ──────────────────────────────────────────────────────

TASK_EASY = {
    "task_id": "risk_identification",
    "task_description": (
        "TASK (Easy): A supplier factory fire has just been reported. "
        "Your job is to identify ALL orders that are now at risk because they "
        "depend on that supplier. Use 'flag_at_risk' actions with order_ids, "
        "then call 'submit_final' when done. "
        "Score = F1(flagged vs truly at-risk orders). Max steps: 8."
    ),
    "max_steps": 8,
    "disruptions": [
        Disruption(
            id="D1", disruption_type="supplier_failure",
            description="Factory fire at GlobalParts Inc — all shipments suspended.",
            affected_entity_id="S1", severity=0.9, day_started=1,
        )
    ],
    "suppliers": [
        Supplier(id="S1", name="GlobalParts Inc", products=["widget_A", "widget_B"],
                 reliability=0.95, is_active=False,
                 stock={"widget_A": 0, "widget_B": 0}),
        Supplier(id="S2", name="ReliaCo", products=["widget_C", "gadget_X"],
                 reliability=0.85, is_active=True,
                 stock={"widget_C": 500, "gadget_X": 200}),
    ],
    "warehouses": [
        Warehouse(id="W1", name="East Hub", location="New York",
                  capacity=1000, inventory={"widget_A": 50, "widget_C": 200}),
        Warehouse(id="W2", name="West Hub", location="Los Angeles",
                  capacity=1000, inventory={"widget_B": 30, "gadget_X": 100}),
    ],
    "orders": [
        Order(id="O1", customer="MegaStore", product="widget_A", quantity=40,
              deadline_day=3, priority=Priority.CRITICAL,
              supplier_id="S1", warehouse_id="W1"),
        Order(id="O2", customer="QuickShop", product="widget_C", quantity=100,
              deadline_day=4, priority=Priority.HIGH,
              supplier_id="S2", warehouse_id="W1"),
        Order(id="O3", customer="TechCorp", product="widget_B", quantity=25,
              deadline_day=2, priority=Priority.CRITICAL,
              supplier_id="S1", warehouse_id="W2"),
        Order(id="O4", customer="LocalMart", product="gadget_X", quantity=50,
              deadline_day=5, priority=Priority.MEDIUM,
              supplier_id="S2", warehouse_id="W2"),
        Order(id="O5", customer="BigBox", product="widget_A", quantity=10,
              deadline_day=6, priority=Priority.LOW,
              supplier_id="S1", warehouse_id="W1"),
    ],
    "budget": 100_000.0,
    "at_risk_order_ids": {"O1", "O3", "O5"},   # ground truth
}

TASK_MEDIUM = {
    "task_id": "inventory_reallocation",
    "task_description": (
        "TASK (Medium): West Hub warehouse is flooded and going offline in 1 day. "
        "You have a $50,000 budget to transfer inventory to East Hub so that "
        "CRITICAL and HIGH priority orders can still be fulfilled. "
        "Use 'transfer_inventory' actions (cost $500/transfer), then "
        "'fulfill_order' when inventory is in place, finally 'submit_final'. "
        "Score = weighted fulfillment rate of CRITICAL+HIGH orders. Max steps: 12."
    ),
    "max_steps": 12,
    "disruptions": [
        Disruption(
            id="D2", disruption_type="warehouse_damage",
            description="West Hub flooding — warehouse goes offline at end of day 2.",
            affected_entity_id="W2", severity=0.8, day_started=1,
        )
    ],
    "suppliers": [
        Supplier(id="S1", name="GlobalParts Inc", products=["widget_A", "widget_B"],
                 reliability=0.9, is_active=True,
                 stock={"widget_A": 300, "widget_B": 200}),
        Supplier(id="S2", name="ReliaCo", products=["widget_C"],
                 reliability=0.85, is_active=True, stock={"widget_C": 400}),
    ],
    "warehouses": [
        Warehouse(id="W1", name="East Hub", location="New York",
                  capacity=2000, inventory={"widget_A": 100, "widget_C": 150}),
        Warehouse(id="W2", name="West Hub", location="Los Angeles",
                  capacity=1000, inventory={"widget_B": 200, "widget_A": 80},
                  is_operational=True),
    ],
    "orders": [
        Order(id="O1", customer="HospitalNet", product="widget_B", quantity=150,
              deadline_day=3, priority=Priority.CRITICAL,
              supplier_id="S1", warehouse_id="W2"),
        Order(id="O2", customer="CityGov", product="widget_A", quantity=60,
              deadline_day=3, priority=Priority.CRITICAL,
              supplier_id="S1", warehouse_id="W2"),
        Order(id="O3", customer="SchoolBoard", product="widget_C", quantity=100,
              deadline_day=4, priority=Priority.HIGH,
              supplier_id="S2", warehouse_id="W1"),
        Order(id="O4", customer="Boutique", product="widget_A", quantity=20,
              deadline_day=5, priority=Priority.MEDIUM,
              supplier_id="S1", warehouse_id="W1"),
        Order(id="O5", customer="Startup", product="widget_B", quantity=30,
              deadline_day=6, priority=Priority.LOW,
              supplier_id="S1", warehouse_id="W2"),
    ],
    "budget": 50_000.0,
    "priority_weights": {Priority.CRITICAL: 1.0, Priority.HIGH: 0.6,
                         Priority.MEDIUM: 0.3, Priority.LOW: 0.1},
}

TASK_HARD = {
    "task_id": "crisis_recovery",
    "task_description": (
        "TASK (Hard): Multi-day supply chain crisis. You have 7 days, $80,000 budget, "
        "and 3 active disruptions hitting simultaneously: supplier failure, warehouse "
        "damage, and a transport delay. You must advance days, reallocate resources, "
        "expedite suppliers ($2000 each), transfer inventory ($500 each), fulfill orders, "
        "and cancel low-priority orders if needed. "
        "Final score = 0.5*fulfillment_rate + 0.3*cost_efficiency + 0.2*speed_bonus. "
        "Max steps: 20."
    ),
    "max_steps": 20,
    "disruptions": [
        Disruption(id="D1", disruption_type="supplier_failure",
                   description="PrimeParts bankrupt — 40% of components unavailable.",
                   affected_entity_id="S3", severity=0.7, day_started=1),
        Disruption(id="D2", disruption_type="warehouse_damage",
                   description="South Hub storm damage — 50% capacity lost.",
                   affected_entity_id="W3", severity=0.5, day_started=1),
        Disruption(id="D3", disruption_type="transport_delay",
                   description="Port strike delays all East→West transfers by 2 days.",
                   affected_entity_id="W1", severity=0.4, day_started=1),
    ],
    "suppliers": [
        Supplier(id="S1", name="GlobalParts Inc", products=["comp_A"],
                 reliability=0.9, is_active=True, stock={"comp_A": 500}),
        Supplier(id="S2", name="ReliaCo", products=["comp_B"],
                 reliability=0.85, is_active=True, stock={"comp_B": 300}),
        Supplier(id="S3", name="PrimeParts", products=["comp_C", "comp_D"],
                 reliability=0.3, is_active=False, stock={"comp_C": 0, "comp_D": 0}),
    ],
    "warehouses": [
        Warehouse(id="W1", name="East Hub", location="New York",
                  capacity=2000, inventory={"comp_A": 200, "comp_B": 100}),
        Warehouse(id="W2", name="West Hub", location="Los Angeles",
                  capacity=1500, inventory={"comp_A": 50, "comp_C": 80}),
        Warehouse(id="W3", name="South Hub", location="Miami",
                  capacity=500, inventory={"comp_D": 60, "comp_B": 40}),
    ],
    "orders": [
        Order(id="O1", customer="AeroSpace Co", product="comp_A", quantity=150,
              deadline_day=3, priority=Priority.CRITICAL, supplier_id="S1", warehouse_id="W1"),
        Order(id="O2", customer="MedDevices", product="comp_B", quantity=80,
              deadline_day=4, priority=Priority.CRITICAL, supplier_id="S2", warehouse_id="W3"),
        Order(id="O3", customer="AutoMaker", product="comp_C", quantity=60,
              deadline_day=5, priority=Priority.HIGH, supplier_id="S3", warehouse_id="W2"),
        Order(id="O4", customer="Electronics", product="comp_D", quantity=40,
              deadline_day=5, priority=Priority.HIGH, supplier_id="S3", warehouse_id="W3"),
        Order(id="O5", customer="RetailChain", product="comp_A", quantity=100,
              deadline_day=6, priority=Priority.MEDIUM, supplier_id="S1", warehouse_id="W2"),
        Order(id="O6", customer="SmallBiz", product="comp_B", quantity=30,
              deadline_day=7, priority=Priority.LOW, supplier_id="S2", warehouse_id="W1"),
    ],
    "budget": 80_000.0,
    "max_days": 7,
}

TASKS = {
    "risk_identification": TASK_EASY,
    "inventory_reallocation": TASK_MEDIUM,
    "crisis_recovery": TASK_HARD,
}


class SupplyChainEnv:
    """OpenEnv-compliant supply chain crisis management environment."""

    def __init__(self, task_id: str = "risk_identification"):
        if task_id not in TASKS:
            raise ValueError(f"Unknown task: {task_id}. Choose from {list(TASKS)}")
        self.task_id = task_id
        self._template = TASKS[task_id]
        self._state: Dict[str, Any] = {}
        self.reset()

    # ── OpenEnv core API ────────────────────────────────────────────────────

    def reset(self) -> Observation:
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

    def step(self, action: Action) -> StepResult:
        if self._state["is_done"]:
            obs = self._build_observation("Episode already done. Call reset().")
            return StepResult(observation=obs, reward=Reward(value=0.001, message="Done"), done=True)

        self._state["steps_taken"] += 1
        reward, message = self._apply_action(action)

        # Check termination
        done = (
            self._state["is_done"]
            or self._state["steps_taken"] >= self._state["max_steps"]
            or action.action_type == "submit_final"
        )
        if done:
            self._state["is_done"] = True
            final_reward = self._compute_final_score()
            reward = final_reward
            message = f"Episode complete. Final score: {final_reward.value:.3f}. {final_reward.message}"

        self._state["total_reward"] += reward.value
        obs = self._build_observation(message)
        return StepResult(observation=obs, reward=reward, done=done,
                          info={"steps_taken": self._state["steps_taken"],
                                "budget_remaining": self._state["budget"]})

    def state(self) -> Dict[str, Any]:
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

    # ── Action handlers ─────────────────────────────────────────────────────

    def _apply_action(self, action: Action) -> Tuple[Reward, str]:
        at = action.action_type
        p = action.parameters

        if at == "flag_at_risk":
            return self._action_flag_at_risk(p)
        elif at == "transfer_inventory":
            return self._action_transfer(p)
        elif at == "expedite_supplier":
            return self._action_expedite(p)
        elif at == "fulfill_order":
            return self._action_fulfill(p)
        elif at == "cancel_order":
            return self._action_cancel(p)
        elif at == "advance_day":
            return self._action_advance_day()
        elif at == "submit_final":
            return Reward(value=0.001, message="Submitting..."), "Finalizing episode..."
        else:
            return Reward(value=0.001, message=f"Unknown action: {at}"), f"Unknown action type: {at}"

    def _action_flag_at_risk(self, p: Dict) -> Tuple[Reward, str]:
        order_ids = p.get("order_ids", [])
        if isinstance(order_ids, str):
            order_ids = [order_ids]
        flagged = set(order_ids)
        self._state["flagged_order_ids"].update(flagged)
        for o in self._state["orders"]:
            if o.id in flagged:
                o.is_flagged_at_risk = True

        if self.task_id == "risk_identification":
            ground_truth = self._template.get("at_risk_order_ids", set())
            correct_flags = self._state["flagged_order_ids"] & ground_truth
            false_flags = self._state["flagged_order_ids"] - ground_truth
            precision = len(correct_flags) / max(len(self._state["flagged_order_ids"]), 1)
            recall = len(correct_flags) / max(len(ground_truth), 1)
            partial = 0.5 * (precision + recall) * 0.3
            return Reward(value=max(0.001, min(0.999, min(partial, 0.3))),
                          components={"precision": precision, "recall": recall},
                          message=f"Flagged {len(flagged)} orders. {len(false_flags)} false positives so far."), \
                   f"Flagged orders: {list(flagged)}"
        return Reward(value=0.05, message="Orders flagged."), f"Flagged: {list(flagged)}"

    def _action_transfer(self, p: Dict) -> Tuple[Reward, str]:
        cost = 500.0
        if self._state["budget"] < cost:
            return Reward(value=0.001, message="Insufficient budget"), "Transfer failed: no budget."
        from_id = p.get("from_warehouse_id", "")
        to_id = p.get("to_warehouse_id", "")
        product = p.get("product", "")
        qty = int(p.get("quantity", 0))

        src = next((w for w in self._state["warehouses"] if w.id == from_id), None)
        dst = next((w for w in self._state["warehouses"] if w.id == to_id), None)
        if not src or not dst:
            return Reward(value=0.001, message="Invalid warehouse IDs"), "Transfer failed: invalid warehouses."
        if src.inventory.get(product, 0) < qty:
            available = src.inventory.get(product, 0)
            qty = available
        if qty <= 0:
            return Reward(value=0.001, message="Nothing to transfer"), "No inventory to transfer."

        src.inventory[product] = src.inventory.get(product, 0) - qty
        dst.inventory[product] = dst.inventory.get(product, 0) + qty
        self._state["budget"] -= cost
        partial = min(qty / 100, 0.999) * 0.1
        return Reward(value=max(0.001, partial), message=f"Transferred {qty} {product}",
                      components={"transfer_partial": partial}), \
               f"Moved {qty} {product} from {from_id} to {to_id}. Cost: ${cost:.0f}"

    def _action_expedite(self, p: Dict) -> Tuple[Reward, str]:
        cost = 2000.0
        supplier_id = p.get("supplier_id", "")
        if self._state["budget"] < cost:
            return Reward(value=0.001, message="Insufficient budget"), "Expedite failed: no budget."
        sup = next((s for s in self._state["suppliers"] if s.id == supplier_id), None)
        if not sup:
            return Reward(value=0.001, message="Supplier not found"), f"No supplier: {supplier_id}"
        if supplier_id in self._state["expedited_suppliers"]:
            return Reward(value=0.001, message="Already expedited"), "Already expedited this supplier."
        sup.is_active = True
        sup.reliability = min(sup.reliability + 0.2, 0.999)
        for product in sup.products:
            sup.stock[product] = sup.stock.get(product, 0) + 200
        self._state["budget"] -= cost
        self._state["expedited_suppliers"].add(supplier_id)
        return Reward(value=0.15, message="Supplier expedited",
                      components={"expedite_bonus": 0.15}), \
               f"Expedited {sup.name}. Restocked +200 units each. Cost: ${cost:.0f}"

    def _action_fulfill(self, p: Dict) -> Tuple[Reward, str]:
        order_id = p.get("order_id", "")
        order = next((o for o in self._state["orders"] if o.id == order_id), None)
        if not order:
            return Reward(value=0.001, message="Order not found"), f"No order: {order_id}"
        if order.is_fulfilled or order.id in self._state["fulfilled_orders"]:
            return Reward(value=0.001, message="Already fulfilled"), "Order already fulfilled."
        if order.id in self._state["cancelled_orders"]:
            return Reward(value=0.001, message="Order cancelled"), "Cannot fulfill cancelled order."

        wh = next((w for w in self._state["warehouses"] if w.id == order.warehouse_id), None)
        if not wh or not wh.is_operational:
            return Reward(value=0.001, message="Warehouse offline"), "Warehouse not operational."
        if wh.inventory.get(order.product, 0) < order.quantity:
            have = wh.inventory.get(order.product, 0)
            return Reward(value=0.05, message="Insufficient inventory"), \
                   f"Need {order.quantity} {order.product}, only {have} available."

        wh.inventory[order.product] -= order.quantity
        order.is_fulfilled = True
        self._state["fulfilled_orders"].add(order_id)
        priority_bonus = {Priority.CRITICAL: 0.25, Priority.HIGH: 0.15,
                          Priority.MEDIUM: 0.08, Priority.LOW: 0.03}[order.priority]
        day_bonus = max(0, (order.deadline_day - self._state["day"]) * 0.01)
        reward_val = max(0.001, min(0.999, min(priority_bonus + day_bonus, 0.3)))
        return Reward(value=reward_val, message=f"Order {order_id} fulfilled!",
                      components={"priority_bonus": priority_bonus, "day_bonus": day_bonus}), \
               f"✓ Fulfilled order {order_id} for {order.customer}"

    def _action_cancel(self, p: Dict) -> Tuple[Reward, str]:
        order_id = p.get("order_id", "")
        order = next((o for o in self._state["orders"] if o.id == order_id), None)
        if not order or order.is_fulfilled:
            return Reward(value=0.001, message="Invalid cancel"), "Cannot cancel."
        self._state["cancelled_orders"].add(order_id)
        penalty = {Priority.CRITICAL: 0.2, Priority.HIGH: 0.1,
                   Priority.MEDIUM: 0.03, Priority.LOW: 0.0}[order.priority]
        return Reward(value=0.001, message=f"Cancelled {order_id}, penalty {penalty:.2f}",
                      components={"cancel_penalty": -penalty}), \
               f"Cancelled order {order_id}. Priority penalty: {penalty:.2f}"

    def _action_advance_day(self) -> Tuple[Reward, str]:
        if self.task_id != "crisis_recovery":
            return Reward(value=0.001, message="advance_day only for crisis_recovery"), \
                   "advance_day only valid in crisis_recovery task."
        max_days = self._template.get("max_days", 7)
        if self._state["day"] >= max_days:
            self._state["is_done"] = True
            return Reward(value=0.001, message="Max days reached"), "All days elapsed."
        self._state["day"] += 1
        penalty = 0.0
        for o in self._state["orders"]:
            if (o.deadline_day < self._state["day"]
                    and not o.is_fulfilled
                    and o.id not in self._state["cancelled_orders"]
                    and o.priority == Priority.CRITICAL):
                penalty += 0.05
        reward_val = max(0.001, min(0.999, max(-penalty, -0.2) + 0.5))
        return Reward(value=reward_val,
                      message=f"Advanced to day {self._state['day']}. Penalty: {penalty:.2f}"), \
               f"Day {self._state['day']} begins. Deadline penalties: {penalty:.2f}"

    # ── Final scoring ────────────────────────────────────────────────────────

    def _compute_final_score(self) -> Reward:
        if self.task_id == "risk_identification":
            return self._score_easy()
        elif self.task_id == "inventory_reallocation":
            return self._score_medium()
        else:
            return self._score_hard()

    def _score_easy(self) -> Reward:
        ground_truth = self._template.get("at_risk_order_ids", set())
        flagged = self._state["flagged_order_ids"]
        tp = len(flagged & ground_truth)
        fp = len(flagged - ground_truth)
        fn = len(ground_truth - flagged)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-6)
        return Reward(value=round(max(0.001, min(0.999, f1)), 4),
                      components={"precision": precision, "recall": recall, "f1": f1},
                      message=f"F1={f1:.3f} | TP={tp} FP={fp} FN={fn}")

    def _score_medium(self) -> Reward:
        weights = self._template.get("priority_weights", {})
        total_w, earned_w = 0.0, 0.0
        for o in self._state["orders"]:
            w = weights.get(o.priority, 0.0)
            total_w += w
            if o.id in self._state["fulfilled_orders"]:
                earned_w += w
        fulfillment = earned_w / max(total_w, 1e-6)
        cost_used = self._template["budget"] - self._state["budget"]
        budget_efficiency = 1.0 - (cost_used / max(self._template["budget"], 1))
        score = 0.7 * fulfillment + 0.3 * budget_efficiency
        return Reward(value=round(max(0.001, min(0.999, score)), 4),
                      components={"fulfillment": fulfillment, "budget_efficiency": budget_efficiency},
                      message=f"Weighted fulfillment={fulfillment:.3f}, cost_eff={budget_efficiency:.3f}")

    def _score_hard(self) -> Reward:
        orders = self._state["orders"]
        total, fulfilled = len(orders), len(self._state["fulfilled_orders"])
        fulfillment_rate = fulfilled / max(total, 1)
        cost_used = self._template["budget"] - self._state["budget"]
        cost_efficiency = 1.0 - min(cost_used / self._template["budget"], 1.0)
        speed_bonus = 0.0
        for o in self._state["orders"]:
            if o.id in self._state["fulfilled_orders"] and o.deadline_day >= self._state["day"]:
                speed_bonus += 1.0 / max(total, 1)
        score = (0.5 * fulfillment_rate + 0.3 * cost_efficiency + 0.2 * speed_bonus)
        return Reward(value=round(max(0.001, min(0.999, score)), 4),
                      components={"fulfillment_rate": fulfillment_rate,
                                  "cost_efficiency": cost_efficiency,
                                  "speed_bonus": speed_bonus},
                      message=f"Fill={fulfillment_rate:.2f} CostEff={cost_efficiency:.2f} Speed={speed_bonus:.2f}")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _build_observation(self, message: str) -> Observation:
        s = self._state
        return Observation(
            day=s["day"],
            budget=s["budget"],
            max_budget=s["max_budget"],
            suppliers=s["suppliers"],
            warehouses=s["warehouses"],
            orders=s["orders"],
            disruptions=s["disruptions"],
            message=message,
            task_id=s["task_id"],
            task_description=s["task_description"],
            steps_taken=s["steps_taken"],
            max_steps=s["max_steps"],
        )
