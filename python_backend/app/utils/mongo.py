from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping, MutableSequence, Union

from bson import ObjectId
from fastapi import HTTPException, status


def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ObjectId format",
        )


JsonLike = Union[Dict[str, Any], List[Any]]


def serialize_mongo(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, Mapping):
        return {k: serialize_mongo(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serialize_mongo(v) for v in obj]
    return obj

