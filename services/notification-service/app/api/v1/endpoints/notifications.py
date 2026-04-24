from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.notification import (
    NotificationCreate, BulkNotificationCreate,
    NotificationResponse, NotificationListResponse,
    ScorePostedEvent, AtRiskAlertEvent,
)
from app.services.notification_service import notification_service

router = APIRouter()


@router.post("/notifications", response_model=NotificationResponse, status_code=201, tags=["Notifications"])
async def send_notification(body: NotificationCreate, db: AsyncSession = Depends(get_db)):
    """Send a single notification to any channel."""
    return await notification_service.create_and_send(db, body)


@router.post("/notifications/bulk", tags=["Notifications"])
async def bulk_send(body: BulkNotificationCreate, db: AsyncSession = Depends(get_db)):
    """Send same notification to multiple recipients."""
    return await notification_service.bulk_send(
        db, body.recipient_ids, body.channel, body.event_type, body.title, body.body
    )


@router.post("/notifications/events/score-posted", status_code=201, tags=["Events"])
async def on_score_posted(event: ScorePostedEvent, db: AsyncSession = Depends(get_db)):
    """Called by score-service when a result is saved. Notifies student of PASS/FAIL."""
    return await notification_service.notify_score_posted(db, event)


@router.post("/notifications/events/at-risk", tags=["Events"])
async def on_at_risk(event: AtRiskAlertEvent, db: AsyncSession = Depends(get_db)):
    """Called by analytics-service to alert at-risk students."""
    return await notification_service.notify_at_risk(db, event)


@router.get("/notifications/{recipient_id}", response_model=NotificationListResponse, tags=["Notifications"])
async def list_notifications(
    recipient_id: str,
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """List all notifications for a recipient."""
    return await notification_service.list_for_recipient(db, recipient_id, unread_only)


@router.patch("/notifications/{recipient_id}/{notif_id}/read", tags=["Notifications"])
async def mark_read(recipient_id: str, notif_id: int, db: AsyncSession = Depends(get_db)):
    return await notification_service.mark_read(db, notif_id, recipient_id)


@router.patch("/notifications/{recipient_id}/read-all", tags=["Notifications"])
async def mark_all_read(recipient_id: str, db: AsyncSession = Depends(get_db)):
    return await notification_service.mark_all_read(db, recipient_id)


@router.get("/health", tags=["System"])
async def health():
    return {"service": "notification-service", "status": "ok"}
