import secrets
import string
from datetime import datetime, timezone

from peewee import AutoField, BooleanField, CharField, DateTimeField, ForeignKeyField, TextField

from app.database import BaseModel
from app.models.user import User

_ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length=6):
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


class Url(BaseModel):
    class Meta:
        table_name = "urls"

    id = AutoField()
    user = ForeignKeyField(User, backref="urls", column_name="user_id")
    short_code = CharField(unique=True, max_length=10)
    original_url = TextField()
    title = CharField(null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "short_code": self.short_code,
            "original_url": self.original_url,
            "title": self.title,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
