"""
The genmrss subcommand can be used to generate an `MRSS
<https://en.wikipedia.org/wiki/Media_RSS>`_ feed which is suitable for `bulk
import into jwplayer
<https://support.jwplayer.com/customer/portal/articles/2798456>`_.

"""
import logging
import urllib.parse
from jinja2 import Environment, select_autoescape
from . import csv as smscsv
from .util import output_stream


LOG = logging.getLogger('genmrss')


#: Jinja2 template for MRSS feed output by ``genmrss``.
MRSS_TEMPLATE_STR = '''
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
    <channel>
        <title>sms2jwplayer generated feed</title>
        <link>http://example.com/index.rss</link>
        <description>SMS Export Feed</description>
{% for item in items %}
        <item>
            <title>{{item.title|sanitise}}</title>
            <link>{{item|url}}</link>
            <description>{{item.description|sanitise}}</description>
            <media:title>{{item.title|sanitise}}</media:title>
            <media:description>{{item.description|sanitise}}</media:description>
            {% if item.image_id %}<media:thumbnail url="{{item|image_url}}" />{% endif %}
            <guid isPermaLink="false">{{item|url}}</guid>
            <media:content url="{{item|url}}" />
        </item>
{% endfor %}
    </channel>
</rss>
'''.strip()


def sanitise(s, max_length=4096):
    """
    Strip odd characters from a string and sanitise the length to maximise
    chances that the feed parse succeeds.

    """
    # Map control characters to empty string
    s = s.translate(dict.fromkeys(range(32)))

    # Truncate
    s = s[:max_length]
    return s


def main(opts):
    """
    Implementation of the ``sms2jwplayer genmrss`` subcommand. *opts* is an
    options dictionary as returned by :py:func:`docopt.docopt`.

    """
    with open(opts['<csv>']) as f:
        items = smscsv.load(f)
    LOG.info('Loaded %s item(s)', len(items))

    # Sort items by descending last_updated_at
    items.sort(key=lambda item: item.last_updated_at)
    items.reverse()

    limit = int(opts['--limit'])
    offset = int(opts['--offset'])
    items = items[offset:limit+offset]
    LOG.info('Limited feed to {} item(s) starting from offset {}'.format(limit, offset))
    LOG.info('Feed truncated to {} items(s)'.format(len(items)))
    if len(items) > 0:
        LOG.info('Most recent last updated: {}'.format(items[0].last_updated_at))
        LOG.info('Least recent last updated: {}'.format(items[-1].last_updated_at))

    def url(item):
        """Return the URL for an item."""
        path_items = item.filename.strip('/').split('/')
        path_items = path_items[int(opts['--strip-leading']):]
        return urllib.parse.urljoin(opts['--base'] + '/', '/'.join(path_items))

    def image_url(item):
        """Return the URL for an image_id."""
        return urllib.parse.urljoin(opts['--base-image-url'], str(item.image_id))

    env = Environment(autoescape=select_autoescape(
        enabled_extensions=['html', 'xml'],
        default_for_string=True
    ))
    env.filters.update({'url': url, 'sanitise': sanitise, 'image_url': image_url})

    feed_content = env.from_string(MRSS_TEMPLATE_STR).render(
        items=items
    )
    with output_stream(opts) as f:
        f.write(feed_content)
