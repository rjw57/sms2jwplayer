Introduction
============

The `Streaming Media Service <https://sms.cam.ac.uk/>`_ offered by the
University of Cambridge is to be re-architectured to use `jwplayer
<https://www.jwplayer.com/>`_ as a storage backend. This repository contains
tooling to help with this migration.

The jwplayer console allows importing videos via an MRSS feed. In order to
perform the initial import of SMS content to jwplayer, we will generate an
archive MRSS feed of all SMS content. The `MRSS
<https://en.wikipedia.org/wiki/Media_RSS>`_ feed is generated by :any:`genmrss`
from a CSV export.

Jwplayer takes care of de-duplicating videos in the feed in order to obtain only
new feed videos. In this way, we can run the :any:`genmrss command <genmrss>`
regularly and automatically ingest new videos.

Installation
------------

It is recommended that the tool be run inside of a virtualenv:

.. code:: console

    $ virtualenv -p $(which python3) venv
    $ source venv/bin/activate

Once the virtualenv is active, the tool may be checked out with ``git`` and
installed via the ``pip`` command:

.. code:: console

    $ git clone $REPO sms2jwplayer
    $ cd sms2jwplayer
    $ pip install .

Where ``$REPO`` is replaced with the location of the ``sms2jwplayer``
repository.

.. note::

    The ``--editable`` or ``-e`` flag may be passed to ``pip install`` to
    symlink files into the Python package path rather than copy them. This
    allows for local development on the tool.

Running tests
-------------

Tests are run via the `tox <https://tox.readthedocs.io/en/latest/>`_ automation
tool. Firstly, install tox:

.. code:: console

    $ pip install tox

In the repository root, run the ``tox`` command. The default environment runs
tests in whichever Python 3 version is installed and prints coverage
information. Configuration can be found in :download:`the tox.ini file
<../tox.ini>`.

Command line interface
----------------------

.. literalinclude:: ../sms2jwplayer/__init__.py
    :language: docopt
    :start-after: """
    :end-before: """

Generating an MRSS Feed
-----------------------

This tool ships with a script which can be used to automatically export the
current state of the SMS archive into a MRSS feed suitable for passing to
jwplayer. The script can be found at ``scripts/export_sms_feed.sh``.

.. literalinclude:: ../scripts/export_sms_feed.sh
    :start-after: #!/usr/bin/env bash
    :end-before: set -e
    :language: shell

You'll need access to an SMS hosting box in order to run the script. You'll also
need to know where the SMS download archive is hosted. For example, if the
archive is hosted at http://user:pass@example.com/archive and you have have
access to the SMS hosting box as ``user@sms-host-1``, you can generate a
suitable MRSS feed via:

.. code:: console

    $ export_sms_feed.sh user@sms-host-1 http://user:pass@example.com/archive feed.rss

The script will log into the SMS hosting box and extract information for the
feed straight from the Postgres database.

.. note::

    The ``psql`` command-line client must be installed on the SMS hosting box.

After the command completes, a MRSS feed will be present in the ``feed.rss``.
This RSS feed file may then be copied to a web-host so that jwplayer may be
direct at it.

.. seealso::

    `Importing Content in Bulk Using MRSS Feeds
    <https://support.jwplayer.com/customer/portal/articles/2798456>`_ on the
    jwplayer support pages.
