import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from collections import defaultdict

from auth import require_internal
from config import DB_PATH

router = APIRouter(prefix="/radar", tags=["Radar"])


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── 1. SLA BREACH ALERTS ──────────────────────────────────────────────────────
# P1 = 15 min, P2 = 4 hours, P3 = 24 hours (from support policy)
SLA_HOURS = {
    "P1": 0.25,   # 15 minutes
    "P2": 4,
    "P3": 24,
}

@router.get("/sla-breaches")
def sla_breaches(user=Depends(require_internal)):
    """
    Returns open tickets that have breached or are within 2 hours of breaching SLA.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE status != 'CLOSED'")
    tickets = [dict(r) for r in cursor.fetchall()]
    conn.close()

    now = datetime.utcnow()
    breached = []
    at_risk = []

    for t in tickets:
        priority = t.get("priority", "P3")
        sla_hours = SLA_HOURS.get(priority, 24)
        created_raw = t.get("created_at") or t.get("created_date") or t.get("date_created")

        if not created_raw:
            continue

        try:
            # handle both date-only and datetime strings
            if "T" in str(created_raw) or " " in str(created_raw):
                created_at = datetime.fromisoformat(str(created_raw).replace("Z", ""))
            else:
                created_at = datetime.strptime(str(created_raw), "%Y-%m-%d")
        except Exception:
            continue

        deadline = created_at + timedelta(hours=sla_hours)
        hours_remaining = (deadline - now).total_seconds() / 3600

        entry = {
            "ticket_id": t.get("ticket_id"),
            "account_id": t.get("account_id"),
            "priority": priority,
            "status": t.get("status"),
            "description": t.get("description", "")[:120],
            "created_at": str(created_raw),
            "deadline": deadline.isoformat(),
            "hours_remaining": round(hours_remaining, 2),
        }

        if hours_remaining < 0:
            entry["alert"] = "BREACHED"
            breached.append(entry)
        elif hours_remaining <= 2:
            entry["alert"] = "AT_RISK"
            at_risk.append(entry)

    # sort breached by most overdue first
    breached.sort(key=lambda x: x["hours_remaining"])
    at_risk.sort(key=lambda x: x["hours_remaining"])

    return {
        "breached": breached,
        "at_risk": at_risk,
        "total_alerts": len(breached) + len(at_risk)
    }


# ── 2. TICKET CLUSTERS ────────────────────────────────────────────────────────
# Groups open tickets by keyword similarity — no new embeddings needed
CLUSTER_KEYWORDS = {
    "CSV / Bulk Upload": ["csv", "bulk", "upload", "3000", "row", "import"],
    "Pickup Delay": ["pickup", "delay", "late", "missed", "window"],
    "Webhook / Status Lag": ["booked", "webhook", "status", "picked_up", "swiftship"],
    "Cancellation": ["cancel", "cancellation", "fee", "waiver"],
    "Service Credit": ["credit", "refund", "sla", "compensation"],
    "Carrier Fault": ["carrier", "fault", "traffic", "driver"],
    "Invoice / Billing": ["invoice", "billing", "charge", "payment"],
}

@router.get("/clusters")
def ticket_clusters(user=Depends(require_internal)):
    """
    Groups open tickets by topic using keyword matching.
    Flags any cluster with 2+ tickets as a potential incident.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE status != 'CLOSED'")
    tickets = [dict(r) for r in cursor.fetchall()]
    conn.close()

    clusters = defaultdict(list)
    unmatched = []

    for t in tickets:
        text = f"{t.get('description', '')} {t.get('resolution', '')}".lower()
        matched = False
        for cluster_name, keywords in CLUSTER_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                clusters[cluster_name].append({
                    "ticket_id": t.get("ticket_id"),
                    "account_id": t.get("account_id"),
                    "status": t.get("status"),
                    "priority": t.get("priority"),
                    "description": t.get("description", "")[:120],
                })
                matched = True
                break
        if not matched:
            unmatched.append(t.get("ticket_id"))

    result = []
    for name, items in clusters.items():
        result.append({
            "cluster": name,
            "ticket_count": len(items),
            "is_incident": len(items) >= 2,
            "tickets": items,
        })

    # sort by ticket count descending
    result.sort(key=lambda x: x["ticket_count"], reverse=True)

    return {
        "clusters": result,
        "incidents_detected": sum(1 for c in result if c["is_incident"]),
        "unmatched_ticket_ids": unmatched
    }


# ── 3. STUCK ORDERS ───────────────────────────────────────────────────────────
STUCK_BOOKED_HOURS = 2   # flag orders stuck in BOOKED for more than 2 hours

@router.get("/stuck-orders")
def stuck_orders(user=Depends(require_internal)):
    """
    Returns orders stuck in BOOKED status beyond the expected webhook window.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE status = 'BOOKED'")
    orders = [dict(r) for r in cursor.fetchall()]
    conn.close()

    now = datetime.utcnow()
    stuck = []

    for o in orders:
        created_raw = (
            o.get("created_at") or
            o.get("created_date") or
            o.get("booking_date") or
            o.get("date_created")
        )

        if not created_raw:
            # include anyway — unknown age is still suspicious
            stuck.append({
                "order_id": o.get("order_id"),
                "account_id": o.get("account_id"),
                "status": o.get("status"),
                "carrier": o.get("carrier"),
                "hours_in_booked": "unknown",
                "alert": "UNKNOWN_AGE"
            })
            continue

        try:
            if "T" in str(created_raw) or " " in str(created_raw):
                created_at = datetime.fromisoformat(str(created_raw).replace("Z", ""))
            else:
                created_at = datetime.strptime(str(created_raw), "%Y-%m-%d")
        except Exception:
            continue

        hours_stuck = (now - created_at).total_seconds() / 3600

        if hours_stuck >= STUCK_BOOKED_HOURS:
            stuck.append({
                "order_id": o.get("order_id"),
                "account_id": o.get("account_id"),
                "status": o.get("status"),
                "carrier": o.get("carrier"),
                "hours_in_booked": round(hours_stuck, 1),
                "alert": "STUCK"
            })

    stuck.sort(key=lambda x: (x["hours_in_booked"] == "unknown", 
                               -(x["hours_in_booked"] if x["hours_in_booked"] != "unknown" else 0)))

    return {
        "stuck_orders": stuck,
        "total": len(stuck)
    }


# ── 4. RADAR SUMMARY (single call for dashboard) ─────────────────────────────
@router.get("/summary")
def radar_summary(user=Depends(require_internal)):
    """
    Single endpoint that returns all 3 radar signals for the dashboard.
    """
    sla = sla_breaches(user=user)
    clusters = ticket_clusters(user=user)
    stuck = stuck_orders(user=user)

    return {
        "sla": {
            "breached": len(sla["breached"]),
            "at_risk": len(sla["at_risk"]),
            "items": sla["breached"] + sla["at_risk"]
        },
        "clusters": {
            "incidents_detected": clusters["incidents_detected"],
            "items": [c for c in clusters["clusters"] if c["is_incident"]]
        },
        "stuck_orders": {
            "total": stuck["total"],
            "items": stuck["stuck_orders"]
        }
    }