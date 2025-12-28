from datetime import datetime, timezone
from uuid import UUID

def build_runtime_context(user_id: UUID) -> str:
    """Build dynamic runtime instructions for a single assistant run. This context is ephemeral and should not be stored in the thread."""

    now = datetime.now(timezone.utc)

    return f"""
Runtime context:
- Today is {now.date().isoformat()}
- Current time is {now.time().isoformat(timespec="minutes")} UTC
- Timezone: UTC

Rules:
- Resolve relative dates (today, tomorrow, next week) based on the date above.
- Always convert dates to absolute ISO 8601 datetimes.
- Use UTC unless the user explicitly specifies another timezone.
""".strip()