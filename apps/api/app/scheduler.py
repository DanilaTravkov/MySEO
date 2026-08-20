import asyncio

from app.db.session import SessionLocal
from app.services.monitoring import claim_due_monitors, run_monitor


async def run_due_monitors() -> tuple[int, int]:
    with SessionLocal() as session:
        claimed = claim_due_monitors(session)

    completed = 0
    failed = 0
    for item in claimed:
        with SessionLocal() as session:
            try:
                await run_monitor(
                    session,
                    item.monitor_id,
                    trigger="scheduled",
                    scheduled_for=item.scheduled_for,
                )
                completed += 1
            except Exception:  # The next claimed monitor must still be processed.
                failed += 1
    return completed, failed


async def main() -> None:
    completed, failed = await run_due_monitors()
    print(f"monitor scheduler: {completed} completed, {failed} failed")


if __name__ == "__main__":
    asyncio.run(main())
