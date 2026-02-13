from datetime import date
from sqlalchemy.orm import Session

from app.models.strategic.plan import StrategicPlan, PlanStatus
from app.core.permissions import Permission


class DashboardService:
    @staticmethod
    def get_strategic_overview(db: Session) -> dict:
        today = date.today()
        plans = db.query(StrategicPlan).all()
        total = len(plans)
        status_counts = {status.value: 0 for status in PlanStatus}
        status_progress: dict[str, list[float]] = {status.value: [] for status in PlanStatus}
        upcoming = []
        for plan in plans:
            status = plan.status.value if plan.status else "draft"
            status_counts.setdefault(status, 0)
            status_counts[status] += 1
            progress = plan.get_progress()
            status_progress.setdefault(status, []).append(progress)
            if plan.end_date and plan.end_date >= today and plan.status == PlanStatus.ACTIVE:
                upcoming.append({
                    "id": plan.id,
                    "name": plan.name,
                    "end_date": plan.end_date,
                    "days_remaining": (plan.end_date - today).days,
                })

        avg_progress = (
            sum((p for prog_list in status_progress.values() for p in prog_list), 0.0) /
            max(sum(len(lst) for lst in status_progress.values()), 1)
        )

        return {
            "total_plans": total,
            "average_progress": round(avg_progress, 2),
            "status_counts": status_counts,
            "status_progress": {
                status: round((sum(lst) / len(lst)) if lst else 0.0, 2)
                for status, lst in status_progress.items()
            },
            "upcoming_deadlines": sorted(upcoming, key=lambda x: x["days_remaining"])[:5],
        }
*** End of File
