from datetime import datetime, timezone

from peewee import AutoField, CharField, DateTimeField

from app.database import BaseModel


class User(BaseModel):
    class Meta:
        table_name = "users"

    id = AutoField()
    username = CharField(unique=True)
    email = CharField(unique=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
