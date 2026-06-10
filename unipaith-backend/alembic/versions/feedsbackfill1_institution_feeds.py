"""Backfill verified content_sources (news/events/social) for deeply-enriched universities

The routine enriched these universities before institution feeds were required, so
their content_sources is NULL and the daily content-ingest job has nothing to fetch
(→ no Updates/Events). This sets content_sources from LIVE-VERIFIED official feeds
(every news RSS confirmed to return XML; every iCal confirmed BEGIN:VCALENDAR with
real events; socials taken from each university's official social directory).

Idempotent + non-clobbering: only writes where content_sources IS NULL, so it never
overwrites a value the routine sets later. No-ops for any institution not present
(e.g. fresh/CI databases).

Revision ID: feedsbackfill1
Revises: pennprof3
"""

import json

import sqlalchemy as sa

from alembic import op

revision = "feedsbackfill1"
down_revision = "pennprof3"
branch_labels = None
depends_on = None


# Institution name → content_sources. URLs verified live 2026-06-10.
# Princeton has no public events feed (verified), so events_feed is omitted.
_FEEDS: dict[str, dict] = {
    "Harvard University": {
        "news_rss": "https://news.harvard.edu/gazette/feed/",
        "events_feed": {"url": "https://www.trumba.com/calendars/gazette.ics", "type": "ical"},
        "social": {
            "instagram": "https://www.instagram.com/harvard/",
            "linkedin": "https://www.linkedin.com/school/harvard-university/",
            "x": "https://x.com/harvard",
            "youtube": "https://www.youtube.com/harvard",
            "facebook": "https://www.facebook.com/Harvard/",
        },
    },
    "Stanford University": {
        "news_rss": "https://news.stanford.edu/feed",
        "events_feed": {"url": "https://events.stanford.edu/calendar.ics", "type": "ical"},
        "social": {
            "instagram": "https://www.instagram.com/stanford/",
            "linkedin": "https://www.linkedin.com/school/stanford-university/",
            "x": "https://x.com/stanford",
            "youtube": "https://www.youtube.com/@stanford",
            "facebook": "https://www.facebook.com/stanford",
        },
    },
    "Yale University": {
        "news_rss": "https://news.yale.edu/news-rss",
        "events_feed": {"url": "https://events.yale.edu/calendar/1.ics", "type": "ical"},
        "social": {
            "instagram": "https://www.instagram.com/yale/",
            "linkedin": "https://www.linkedin.com/school/yale-university/",
            "x": "https://x.com/yale",
            "youtube": "https://www.youtube.com/user/YaleUniversity",
            "facebook": "https://www.facebook.com/YaleUniversity",
        },
    },
    "Princeton University": {
        "news_rss": "https://www.princeton.edu/feed",
        "social": {
            "instagram": "https://www.instagram.com/princeton/",
            "linkedin": "https://www.linkedin.com/school/princeton-university/",
            "x": "https://x.com/princeton",
            "youtube": "https://www.youtube.com/princeton",
            "facebook": "https://www.facebook.com/PrincetonU",
        },
    },
    "Columbia University in the City of New York": {
        "news_rss": "https://news.columbia.edu/news/rss.xml",
        "events_feed": {
            "url": "https://events.columbia.edu/feeder/main/listEvents.do?days=30&format=text/calendar",
            "type": "ical",
        },
        "social": {
            "instagram": "https://www.instagram.com/columbia/",
            "linkedin": "https://www.linkedin.com/school/columbia-university/",
            "x": "https://x.com/columbia",
            "youtube": "https://www.youtube.com/user/columbiauniversity",
            "facebook": "https://www.facebook.com/columbia/",
        },
    },
    "University of Chicago": {
        "news_rss": "http://feeds.feedburner.com/UChicago",
        "events_feed": {"url": "https://events.uchicago.edu/live/ical/events", "type": "ical"},
        "social": {
            "instagram": "https://www.instagram.com/uchicago/",
            "linkedin": "https://www.linkedin.com/school/uchicago/",
            "x": "https://x.com/UChicago",
            "youtube": "https://www.youtube.com/channel/UCGINcKuFbysZAslgL46KeOA",
            "facebook": "https://www.facebook.com/uchicago/",
        },
    },
    "University of California-Berkeley": {
        "news_rss": "https://news.berkeley.edu/feed/",
        "events_feed": {"url": "https://events.berkeley.edu/live/ical/events", "type": "ical"},
        "social": {
            "instagram": "https://www.instagram.com/ucberkeleyofficial/",
            "linkedin": "https://www.linkedin.com/school/uc-berkeley/",
            "x": "https://x.com/UCBerkeley",
            "youtube": "https://www.youtube.com/channel/UCZAXKyvvIV4uU4YvP5dmrmA",
            "facebook": "https://www.facebook.com/UCBerkeley",
        },
    },
    "California Institute of Technology": {
        "news_rss": "https://www.caltech.edu/about/news/rss/",
        "events_feed": {
            "url": "https://www.caltech.edu/campus-life-events/calendar/ical",
            "type": "ical",
        },
        "social": {
            "instagram": "https://www.instagram.com/caltechedu",
            "linkedin": "https://www.linkedin.com/school/california-institute-of-technology/",
            "x": "https://x.com/caltech",
            "youtube": "https://www.youtube.com/caltech",
            "facebook": "https://www.facebook.com/californiainstituteoftechnology",
        },
    },
}


def upgrade() -> None:
    bind = op.get_bind()
    stmt = sa.text(
        "UPDATE institutions SET content_sources = CAST(:cs AS jsonb) "
        "WHERE name = :name "
        "AND (content_sources IS NULL OR jsonb_typeof(content_sources) = 'null')"
    )
    for name, cs in _FEEDS.items():
        bind.execute(stmt, {"cs": json.dumps(cs), "name": name})


def downgrade() -> None:
    # Data-only backfill; no structural rollback.
    pass
