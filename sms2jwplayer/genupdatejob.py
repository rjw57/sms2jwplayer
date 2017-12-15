"""
The genupdatejob subcommand examines video metadata from jwplayer and the current SMS export and
generates a list of updates which should be applied.

It outputs a single JSON object with the following schema:

.. code:: json

    {
        "updates": [
            ...
            {
                "key": <jwplayer key>,
                "custom": {
                    <dictionary of custom properties to set>
                }
            },
            ...
        ],
    }

"""
import json
import logging
from urllib.parse import urlsplit

from . import csv as smscsv
from .util import output_stream, get_key_path


LOG = logging.getLogger('genmrss')


def main(opts):
    videos = []
    for metadata_fn in opts['<metadata>']:
        with open(metadata_fn) as f:
            videos.extend(json.load(f).get('videos', []))
    LOG.info('Loaded metadata for %s videos', len(videos))

    # Load items keyed by stripped path
    strip_from = int(opts['--strip-leading'])
    LOG.info('Stripping leading %s component(s) from filename', strip_from)
    with open(opts['<csv>']) as f:
        items = dict(
            ('/'.join(item.filename.strip('/').split('/')[strip_from:]), item)
            for item in smscsv.load(f)
        )
    LOG.info('Loaded %s media item(s) from export', len(items))

    with output_stream(opts) as fobj:
        process_videos(fobj, items, videos)


def process_videos(fobj, items, videos):
    """
    Process video metadata records with reference to a dictionary of media items keyed by the
    stripped path. Write results to file as JSON document.

    """
    # Statistics we record
    n_skipped = 0
    n_unmatched = 0
    n_matched = 0

    updates = []

    # Match jwplayer videos to SMS items
    for video in videos:
        # Find original fetch URL
        orig_url = get_key_path(video, 'custom.import_guid')
        if orig_url is None:
            n_skipped += 1
            continue

        # Parse path components
        path_components = urlsplit(orig_url).path.split('/')

        # Try to find item by joining path components
        item = None
        while len(path_components) > 0 and item is None:
            item = items.get('/'.join(path_components))
            path_components = path_components[1:]

        if item is None:
            n_unmatched += 1
            continue

        # video and item now match
        n_matched += 1

        # form list of expected custom properties
        custom_props = {
            'sms_media_id': item.media_id,
            'sms_clip_id': item.clip_id,
        }

        # remove those which match
        for k, v in list(custom_props.items()):
            if get_key_path(video, 'custom.' + k) == v:
                del custom_props[k]

        # write a row if there is work to do
        if len(custom_props) > 0:
            updates.append({'key': get_key_path(video, 'key'), 'custom': custom_props})

    LOG.info('Number of jwplayer videos matched to SMS media items: %s', n_matched)
    LOG.info('Number of jwplayer videos not matched to SMS media items: %s', n_unmatched)
    LOG.info('Number of jwplayer videos with no import URL: %s', n_skipped)
    LOG.info('Number of video updates: %s', len(updates))

    json.dump({'updates': updates}, fobj)