from pydantic import BaseModel
from typing import Literal


class ProcessRequest(BaseModel):
    location_id: Literal["fci", "faie"]