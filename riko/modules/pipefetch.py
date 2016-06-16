# -*- coding: utf-8 -*-
# vim: sw=4:ts=4:expandtab
"""
riko.modules.pipefetch
~~~~~~~~~~~~~~~~~~~~~~
Provides functions for fetching RSS feeds.

Lets you specify an RSS news feed as input. This module understands feeds in
RSS, Atom, and RDF formats. Feeds contain one or more items.

Examples:
    basic usage::

        >>> from riko import get_path
        >>> from riko.modules.pipefetch import pipe
        >>> next(pipe(conf={'url': get_path('feed.xml')}))['title']
        u'Donations'

Attributes:
    OPTS (dict): The default pipe options
    DEFAULTS (dict): The default parser options
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

try:
    import speedparser
except ImportError:
    import feedparser as speedparser


from builtins import *
from six.moves.urllib.request import urlopen
from twisted.internet.defer import inlineCallbacks, returnValue

from . import processor
from riko.lib import utils
from riko.twisted import utils as tu
from riko.lib.log import Logger

OPTS = {'ftype': 'none'}
DEFAULTS = {'sleep': 0}
logger = Logger(__name__).logger
intersection = [
    'author', 'author.name', 'author.uri', 'dc:creator', 'id', 'link',
    'pubDate', 'summary', 'title', 'y:id', 'y:published', 'y:title']


@inlineCallbacks
def asyncParser(_, objconf, skip, **kwargs):
    """ Asynchronously parses the pipe content

    Args:
        _ (None): Ignored
        objconf (obj): The pipe configuration (an Objectify instance)
        skip (bool): Don't parse the content
        kwargs (dict): Keyword arguments

    Kwargs:
        stream (dict): The original item
        conf (dict): The pipe configuration

    Returns:
        Deferred: twisted.internet.defer.Deferred Tuple(Iter[dict], bool)

    Examples:
        >>> from twisted.internet.task import react
        >>> from riko import get_path
        >>> from riko.lib.utils import Objectify
        >>>
        >>> def run(reactor):
        ...     callback = lambda x: print(next(x[0])['title'])
        ...     objconf = Objectify({'url': get_path('feed.xml'), 'sleep': 0})
        ...     kwargs = {'stream': {}}
        ...     d = asyncParser(None, objconf, False, **kwargs)
        ...     return d.addCallbacks(callback, logger.error)
        >>>
        >>> try:
        ...     react(run, _reactor=tu.FakeReactor())
        ... except SystemExit:
        ...     pass
        ...
        Donations
    """
    if skip:
        stream = kwargs['stream']
    else:
        url = utils.get_abspath(objconf.url)
        content = yield tu.urlRead(url, delay=objconf.sleep)
        parsed = speedparser.parse(content)
        stream = utils.gen_entries(parsed)

    result = (stream, skip)
    returnValue(result)


def parser(_, objconf, skip, **kwargs):
    """ Parses the pipe content

    Args:
        _ (None): Ignored
        objconf (obj): The pipe configuration (an Objectify instance)
        skip (bool): Don't parse the content
        kwargs (dict): Keyword arguments

    Kwargs:
        stream (dict): The original item
        conf (dict): The pipe configuration

    Returns:
        Tuple(Iter[dict], bool): Tuple of (stream, skip)

    Examples:
        >>> from riko import get_path
        >>> from riko.lib.utils import Objectify
        >>>
        >>> objconf = Objectify({'url': get_path('feed.xml'), 'sleep': 0})
        >>> kwargs = {'stream': {}}
        >>> result, skip = parser(None, objconf, False, **kwargs)
        >>> next(result)['title']
        u'Donations'
    """
    if skip:
        stream = kwargs['stream']
    else:
        url = utils.get_abspath(objconf.url)
        context = utils.SleepyDict(delay=objconf.sleep)
        content = urlopen(url, context=context).read()
        parsed = speedparser.parse(content)
        stream = utils.gen_entries(parsed)

    return stream, skip


@processor(DEFAULTS, async=True, **OPTS)
def asyncPipe(*args, **kwargs):
    """A source that asynchronously fetches and parses a feed to return the
    entries.

    Args:
        item (dict): The entry to process
        kwargs (dict): The keyword arguments passed to the wrapper

    Kwargs:
        conf (dict): The pipe configuration. Must contain the key 'url'. May
            contain the key 'sleep'.

            url (str): The web site to fetch.
            sleep (flt): Amount of time to sleep (in secs) before fetching the
                url. Useful for simulating network latency. Default: 0.


    Returns:
        Deferred: twisted.internet.defer.Deferred iterator of items

    Examples:
        >>> from twisted.internet.task import react
        >>> from riko import get_path
        >>>
        >>> i = intersection
        >>>
        >>> def run(reactor):
        ...     callback = lambda x: print(set(next(x).keys()).issuperset(i))
        ...     d = asyncPipe(conf={'url': get_path('feed.xml')})
        ...     return d.addCallbacks(callback, logger.error)
        >>>
        >>> try:
        ...     react(run, _reactor=tu.FakeReactor())
        ... except SystemExit:
        ...     pass
        ...
        True
    """
    return asyncParser(*args, **kwargs)


@processor(DEFAULTS, **OPTS)
def pipe(*args, **kwargs):
    """A source that fetches and parses a feed to return the entries.

    Args:
        item (dict): The entry to process
        kwargs (dict): The keyword arguments passed to the wrapper

    Kwargs:
        conf (dict): The pipe configuration. Must contain the key 'url'. May
            contain the key 'sleep'.

            url (str): The web site to fetch.
            sleep (flt): Amount of time to sleep (in secs) before fetching the
                url. Useful for simulating network latency. Default: 0.

    Returns:
        dict: an iterator of items

    Examples:
        >>> from riko import get_path
        >>>
        >>> keys = next(pipe(conf={'url': get_path('feed.xml')})).keys()
        >>> set(keys).issuperset(intersection)
        True
    """
    return parser(*args, **kwargs)