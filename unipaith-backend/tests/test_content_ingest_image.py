"""The news-RSS parser captures the cover image from media:content / thumbnail.

News cards render this real source image; items without one stay None (we never
fabricate an image — events in particular have none).
"""

from unipaith.services.content_ingest.rss import NewsRssSource

_RSS_MEDIA_CONTENT = """<?xml version="1.0"?>
<rss xmlns:media="http://search.yahoo.com/mrss/"><channel>
<item>
  <title>AI news</title>
  <link>https://news.mit.edu/2026/x</link>
  <guid>g1</guid>
  <media:content url="https://news.mit.edu/img.jpg" medium="image"/>
</item>
</channel></rss>"""

_RSS_THUMBNAIL = """<?xml version="1.0"?>
<rss xmlns:media="http://search.yahoo.com/mrss/"><channel>
<item>
  <title>Thumb news</title>
  <link>https://news.mit.edu/2026/y</link>
  <guid>g2</guid>
  <media:thumbnail url="https://news.mit.edu/thumb.jpg"/>
</item>
</channel></rss>"""

_RSS_NO_IMAGE = """<?xml version="1.0"?>
<rss><channel>
<item><title>No image</title><link>https://news.mit.edu/2026/z</link><guid>g3</guid></item>
</channel></rss>"""


def test_rss_extracts_media_content_image():
    items = NewsRssSource().parse(_RSS_MEDIA_CONTENT)
    assert items[0].image_url == "https://news.mit.edu/img.jpg"


def test_rss_falls_back_to_media_thumbnail():
    items = NewsRssSource().parse(_RSS_THUMBNAIL)
    assert items[0].image_url == "https://news.mit.edu/thumb.jpg"


def test_rss_no_image_is_none():
    items = NewsRssSource().parse(_RSS_NO_IMAGE)
    assert items[0].image_url is None
