from typing import Dict, Any, Optional
from pydantic import BaseModel, model_validator

class FlinkCdcConfig(BaseModel):
    task_type: str
    name: str
    description: Optional[str]
    task_timeout_seconds: int
    pipeline: Dict[str, Any]
    resources: Dict[str, Any]

    @model_validator(mode="after")
    def check_required_fields(self):
        # Add custom validation logic if needed
        return self
