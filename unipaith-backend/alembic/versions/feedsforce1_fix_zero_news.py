"""Force-set verified, SERVER-FETCHABLE content_sources for universities whose news showed 0.

feedsbackfill1 used only-if-NULL, but the routine had pre-set a newsless content_sources on the
deeply-enriched ones, so it no-op'd them (Yale/Berkeley/Princeton/UChicago/Caltech) — force-set
here with verified feeds (Caltech news de-redirected). Purdue/UCSD use verified university-wide news
feeds confirmed server-fetchable. Stanford/Columbia official news is Cloudflare-gated to servers
(only narrow school feeds exist — omitted to avoid misleading scope) and NYU has no server-fetchable
official news, so those get events/social only. Every URL HTTP 200 to a server UA. FORCE overwrite;
idempotent; no-ops if absent.

Revision ID: feedsforce1
Revises: cornellprof1
"""
# ruff: noqa: E501

import json

import sqlalchemy as sa

from alembic import op

revision = "feedsforce1"
down_revision = "cornellprof1"
branch_labels = None
depends_on = None

_FEEDS = {
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
    "California Institute of Technology": {
        "news_rss": "https://www.caltech.edu/news/rss.xml",
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
    "Purdue University-Main Campus": {
        "news_rss": "https://stories.purdue.edu/feed/",
        "events_feed": {"url": "https://events.purdue.edu/calendar.xml", "type": "rss"},
        "social": {
            "instagram": "https://www.instagram.com/lifeatpurdue/",
            "linkedin": "https://www.linkedin.com/edu/purdue-university-18357",
            "x": "https://twitter.com/LifeAtPurdue",
            "youtube": "https://www.youtube.com/purdueuniversity",
            "facebook": "https://www.facebook.com/PurdueUniversity/",
        },
    },
    "University of California-San Diego": {
        "news_rss": "https://today.ucsd.edu/rss/topstories",
        "events_feed": {"url": "https://calendar.ucsd.edu/calendar.ics", "type": "ical"},
        "social": {
            "instagram": "https://instagram.com/ucsandiego",
            "facebook": "https://facebook.com/ucsandiego",
            "x": "https://x.com/UCSanDiego",
            "youtube": "https://youtube.com/ucsandiego",
            "linkedin": "https://www.linkedin.com/company/university-of-california-at-san-diego/",
        },
    },
    "New York University": {
        "events_feed": {"url": "https://events.nyu.edu/live/rss/events", "type": "rss"},
        "social": {
            "instagram": "https://www.instagram.com/nyuniversity/",
            "linkedin": "https://www.linkedin.com/school/new-york-university/",
            "x": "https://twitter.com/nyuniversity",
            "youtube": "https://www.youtube.com/user/nyu",
            "facebook": "https://www.facebook.com/NYU",
        },
    },
    "Stanford University": {
        "events_feed": {"url": "https://events.stanford.edu/calendar.ics", "type": "ical"},
        "social": {
            "instagram": "https://www.instagram.com/stanford/",
            "linkedin": "https://www.linkedin.com/school/stanford-university/",
            "x": "https://x.com/stanford",
            "youtube": "https://www.youtube.com/@stanford",
            "facebook": "https://www.facebook.com/stanford",
        },
    },
    "Columbia University in the City of New York": {
        "social": {
            "instagram": "https://www.instagram.com/columbia/",
            "linkedin": "https://www.linkedin.com/school/columbia-university/",
            "x": "https://x.com/columbia",
            "youtube": "https://www.youtube.com/user/columbiauniversity",
            "facebook": "https://www.facebook.com/columbia/",
        }
    },
}


def upgrade() -> None:
    bind = op.get_bind()
    stmt = sa.text(
        "UPDATE institutions SET content_sources = CAST(:cs AS jsonb) WHERE name = :name"
    )
    for name, cs in _FEEDS.items():
        bind.execute(stmt, {"cs": json.dumps(cs), "name": name})


def downgrade() -> None:
    pass
