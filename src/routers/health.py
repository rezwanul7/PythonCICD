from fastapi import APIRouter, HTTPException, Request, status

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/startup")
def startup(request: Request):
    if not request.app.state.started:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application has not started",
        )
    return {"status": "started"}


@router.get("/live")
def live():
    return {"status": "alive"}


@router.get("/ready")
def ready(request: Request):
    if not request.app.state.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application is not ready",
        )
    return {"status": "ready"}
