import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException

from app.models.notification import Notification, StatusEnum
from app.schemas.notification import NotificationCreate, ScorePostedEvent, AtRiskAlertEvent

logger = logging.getLogger("notification-service")


class NotificationService:

    async def create_and_send(self, db: AsyncSession, data: NotificationCreate) -> Notification:
        notif = Notification(
            recipient_id    = data.recipient_id,
            recipient_email = data.recipient_email,
            channel         = data.channel,
            event_type      = data.event_type,
            title           = data.title,
            body            = data.body,
            status          = StatusEnum.pending,
        )
        db.add(notif)
        await db.flush()

        # In-app: stored = delivered. Email: log-only in dev (no SMTP configured).
        if data.channel == "email" and data.recipient_email:
            logger.info(f"[EMAIL] To={data.recipient_email} | {data.title}")
        else:
            logger.info(f"[{data.channel.upper()}] → {data.recipient_id} | {data.title}")

        notif.status  = StatusEnum.sent
        notif.sent_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(notif)
        return notif

    async def bulk_send(self, db: AsyncSession, recipient_ids: list[str],
                        channel, event_type, title, body) -> dict:
        sent = 0
        for rid in recipient_ids:
            await self.create_and_send(db, NotificationCreate(
                recipient_id=rid, channel=channel,
                event_type=event_type, title=title, body=body,
            ))
            sent += 1
        return {"sent": sent}

    async def notify_score_posted(self, db: AsyncSession, event: ScorePostedEvent) -> Notification:
        icon  = "✅" if event.pass_fail == "PASS" else "❌"
        title = f"{icon} Result: {event.pass_fail} — {event.total_score}/100"
        body  = (
            f"Student {event.student_id}: total_score={event.total_score}, "
            f"grade={event.grade}, result={event.pass_fail}."
        )
        return await self.create_and_send(db, NotificationCreate(
            recipient_id    = str(event.student_id),
            recipient_email = event.student_email,
            channel         = "email" if event.student_email else "in_app",
            event_type      = "score_posted",
            title=title, body=body,
        ))

    async def notify_at_risk(self, db: AsyncSession, event: AtRiskAlertEvent) -> dict:
        sent = 0
        for s in event.students:
            title = f"⚠️ At-Risk Alert — Student {s['student_id']}"
            body  = (
                f"Student {s['student_id']} is {s.get('risk_level','MEDIUM')} risk. "
                f"Total score: {s.get('total_score','?')}. Please contact for support."
            )
            await self.create_and_send(db, NotificationCreate(
                recipient_id = str(s["student_id"]),
                channel      = "in_app",
                event_type   = "at_risk_alert",
                title=title, body=body,
            ))
            sent += 1
        return {"at_risk_notifications_sent": sent}

    async def list_for_recipient(self, db: AsyncSession, recipient_id: str,
                                  unread_only: bool = False) -> dict:
        q = select(Notification).where(Notification.recipient_id == recipient_id)
        if unread_only:
            q = q.where(Notification.is_read == False)
        q = q.order_by(Notification.created_at.desc())
        items = (await db.execute(q)).scalars().all()
        return {"total": len(items), "items": items}

    async def mark_read(self, db: AsyncSession, notif_id: int, recipient_id: str) -> dict:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notif_id,
                Notification.recipient_id == recipient_id,
            )
        )
        notif = result.scalar_one_or_none()
        if not notif:
            raise HTTPException(404, "Notification not found")
        notif.is_read = True
        return {"message": "Marked as read"}

    async def mark_all_read(self, db: AsyncSession, recipient_id: str) -> dict:
        await db.execute(
            update(Notification)
            .where(Notification.recipient_id == recipient_id, Notification.is_read == False)
            .values(is_read=True)
        )
        return {"message": "All notifications marked as read"}


notification_service = NotificationService()
