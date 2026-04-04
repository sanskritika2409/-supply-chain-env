models_content = """from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum

class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Supplier(BaseModel):
    id: str
    name: str
    products: List[str]
    reliability: float
    is_active: bool = True
    stock: Dict[str, int] = {}

class Warehouse(BaseModel):
    id: str
    name: str
    location: str
    capacity: int
    inventory: Dict[str, int] = {}
    is_operational: bool = True

class Order(BaseModel):
    id: str
    customer: str
    product: str
    quantity: int
    deadline_day: int
    priority: Priority
    supplier_id: str
    warehouse_id: str
    is_fulfilled: bool = False
    is_flagged_at_risk: bool = False

class Disruption(BaseModel):
    id: str
    disruption_type: str
    description: str
    affected_entity_id: str
    severity: float
    day_started: int

class Observation(BaseModel):
    day: int
    budget: float
    max_budget: float
    suppliers: List[Supplier]
    warehouses: List[Warehouse]
    orders: List[Order]
    disruptions: List[Disruption]
    message: str
    task_id: str
    task_description: str
    steps_taken: int
    max_steps: int

class Action(BaseModel):
    action_type: str = Field(description="One of: flag_at_risk, transfer_inventory, expedite_supplier, cancel_order, fulfill_order, advance_day, submit_final")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reasoning: Optional[str] = None

class Reward(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    components: Dict[str, float] = Field(default_factory=dict)
    message: str = ""

class StepResult(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)

class StateResult(BaseModel):
    task_id: str
    day: int
    budget: float
    steps_taken: int
    total_reward: float
    orders_fulfilled: int
    orders_at_risk: int
    active_disruptions: int
    is_done: bool
"""

with open("models.py", "w") as f:
    f.write(models_content)

print("models.py created!")
