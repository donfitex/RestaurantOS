from django.db import IntegrityError, transaction

from .exceptions import Conflict


def insert_unique(manager, lookup, **values):
    """Turn a concurrently claimed unique reference into a workflow conflict."""
    try:
        with transaction.atomic():
            return manager.create(**values)
    except IntegrityError:
        if manager.filter(**lookup).exists():
            raise Conflict("This reference was claimed by another transaction.") from None
        raise
