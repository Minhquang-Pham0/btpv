from pydantic import BaseModel
from typing import List
from datetime import datetime

class LogAssociation(BaseModel):
    log_id: int
    association_id: int
    association_type: str

class Log(BaseModel):
    id: int
    msg: str
    time: datetime

    associations: List[LogAssociation]
