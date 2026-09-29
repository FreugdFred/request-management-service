from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.jobs.publish_events import publish_events
from src.jobs.remove_published_events import remove_published_events

scheduler = AsyncIOScheduler()

scheduler.add_job(
    publish_events,
    trigger="interval",
    seconds=10,
    id="publish-events",
    coalesce=True,
    max_instances=1,
    replace_existing=True,
)

scheduler.add_job(
    remove_published_events,
    trigger="interval",
    minutes=1,
    id="remove-published-events",
    coalesce=True,
    max_instances=1,
    replace_existing=True,
)
