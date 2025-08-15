from typing import List, Optional, Dict, Any, Annotated
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages
from typing import TypedDict

class PricingTier(BaseModel):
    name: str
    monthly_price: Optional[float] = Field(None, description="Monthly price in USD")
    annual_price: Optional[float] = Field(None, description="Annual price in USD")
    user_limit: Optional[int] = Field(None, description="Maximum users")
    features: List[str] = Field(default_factory=list)

class CRMFeatures(BaseModel):
    core_features: List[str] = Field(default_factory=list)
    automation: List[str] = Field(default_factory=list)
    analytics: List[str] = Field(default_factory=list)
    customization: List[str] = Field(default_factory=list)

class Integration(BaseModel):
    name: str
    category: str
    native: bool = False

class CRMData(BaseModel):
    name: str
    pricing_tiers: List[PricingTier] = Field(default_factory=list)
    features: CRMFeatures = Field(default_factory=CRMFeatures)
    integrations: List[Integration] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    best_for: List[str] = Field(default_factory=list)
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)

class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    crm_data: Dict[str, CRMData]
    research_status: Dict[str, bool]
    validation_results: List[Dict[str, Any]]
    final_comparison: Dict[str, Any]
    current_task: str
    iteration_count: int
    error_log: List[Dict[str, Any]]
    convergence_history: List[str]
    trace_id: str
