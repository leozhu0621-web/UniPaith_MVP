"""Unit tests for the content-ingest relevance gate (passes_relevance).

Encodes the user rule: a MIT post/event containing the scope keyword counts;
a random mention (no keyword in the visible text) does not. Curated feeds
(MIT-authoritative topic feeds) bypass the gate; un-keyworded scopes keep all.
"""

from unipaith.services.content_ingest.base import NormalizedItem, passes_relevance


def _item(title="", body="", location=None):
    return NormalizedItem(kind="event", external_id="x", title=title, body=body, location=location)


def test_curated_keeps_all():
    assert passes_relevance(_item(title="Anything at all"), [], curated=True) is True
    assert passes_relevance(_item(title="Anything"), ["sloan"], curated=True) is True


def test_no_keywords_keeps_all():
    assert passes_relevance(_item(title="Anything"), None, curated=False) is True
    assert passes_relevance(_item(title="Anything"), [], curated=False) is True


def test_keyword_in_visible_text_kept():
    assert passes_relevance(_item(title="MIT Sloan info session"), ["sloan"]) is True
    assert (
        passes_relevance(_item(title="Talk", body="Hosted at the Sloan building"), ["sloan"])
        is True
    )
    assert passes_relevance(_item(title="Seminar", location="E62 Sloan"), ["sloan"]) is True


def test_keyword_absent_dropped():
    assert passes_relevance(_item(title="Spring into Writing"), ["sloan"]) is False
    assert passes_relevance(_item(title="Celebrate Juneteenth!"), ["sloan"]) is False


def test_word_boundary_no_substring_false_positive():
    # "Sloane" must not match keyword "sloan".
    assert passes_relevance(_item(title="Prof. Sloane speaks"), ["sloan"]) is False


def test_case_insensitive():
    assert passes_relevance(_item(title="SLOAN reunion"), ["sloan"]) is True


def test_multi_keyword_any_match():
    kws = ["mban", "business analytics", "operations research"]
    assert passes_relevance(_item(title="Business Analytics demo day"), kws) is True
    assert passes_relevance(_item(title="Operations Research seminar"), kws) is True
    assert passes_relevance(_item(title="Poetry reading"), kws) is False
