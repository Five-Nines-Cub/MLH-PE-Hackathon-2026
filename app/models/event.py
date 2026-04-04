import json
from datetime import datetime

from peewee import AutoField, CharField, DateTimeField, ForeignKeyField, TextField

from app.database import BaseModel
from app.models.url import Url
from app.models.user import User


class Event(BaseModel):
    class Meta:
        table_name = "events"

    id = AutoField()
    url = ForeignKeyField(Url, backref="events", column_name="url_id")
    user = ForeignKeyField(User, backref="events", column_name="user_id", null=True)
    event_type = CharField()
    timestamp = DateTimeField(default=datetime.utcnow)
    details = TextField(null=True)

    def to_dict(self):
        return {
            "id": self.id,
            "url_id": self.url_id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "details": json.loads(self.details) if self.details else {},
        }
