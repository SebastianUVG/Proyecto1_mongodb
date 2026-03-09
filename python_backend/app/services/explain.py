from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase


def _contains_stage(plan: Any, stage_name: str) -> bool:
    if isinstance(plan, dict):
        if plan.get("stage") == stage_name:
            return True
        return any(_contains_stage(v, stage_name) for v in plan.values())
    if isinstance(plan, list):
        return any(_contains_stage(v, stage_name) for v in plan)
    return False


async def assert_find_uses_index(
    db: AsyncIOMotorDatabase,
    collection: str,
    filter_: Dict[str, Any],
    sort: Optional[Dict[str, int]] = None,
    projection: Optional[Dict[str, int]] = None,
    skip: int = 0,
    limit: int = 0,
) -> None:
    if os.getenv("ENFORCE_NO_COLLSCAN") not in ("1", "true", "TRUE", "yes", "YES"):
        return

    explain: Dict[str, Any] = {
        "explain": {
            "find": collection,
            "filter": filter_,
            "skip": skip,
            "limit": limit,
        },
        "verbosity": "executionStats",
    }
    if sort:
        explain["explain"]["sort"] = sort
    if projection:
        explain["explain"]["projection"] = projection

    result = await db.command(explain)
    qp = result.get("queryPlanner", {})
    winning = qp.get("winningPlan")
    if winning and _contains_stage(winning, "COLLSCAN"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query rejected: would perform COLLSCAN (no index used).",
        )

