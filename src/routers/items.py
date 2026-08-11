from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
