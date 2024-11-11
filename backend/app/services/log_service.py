from sqlalchemy.orm import Session
from fastapi import Depends
from typing import List
from ..models.entities import Log, LogAssociation, User
from ..db import get_db

class LogService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    async def create_log(self, strIn: str) -> Log:
        log = Log(
            msg = strIn
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    async def create_association(self, current_log: Log, aid: int, atype: str) -> LogAssociation:
        log_association = LogAssociation(
            log_id = current_log.id,
            association_id = aid,
            association_type = atype
        )

        self.db.add(log_association)
        self.db.commit()
        self.db.refresh(current_log)
        self.db.refresh(log_association)
        return log_association
    
    async def get_logs(self, current_user: User) -> List[Log]:
        return self.db.query(Log).all()
    
    async def get_logs_by(self, current_user: User, aid: int, atype: str) -> List[Log]:
        return self.db.query(Log)\
            .filter(Log.associations.any(LogAssociation.association_id == aid), Log.associations.any(LogAssociation.association_type == atype))\
            .all()