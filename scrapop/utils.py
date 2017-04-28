# -*- coding: utf-8 -*-
"""
Utilities for Scrapop module.
"""

import time
import datetime
from numbers import Number

from urlparse import urlparse, urlunparse
from urlparse import urlsplit, urlunsplit
from urlparse import ParseResult

import tldextract

class SanitationHelpers(object):
    """
    A set of utilities related to sanitizing strings.
    """

    @classmethod
    def to_ascii(cls, thing):
        return thing.encode(errors='backslashreplace')

class URLHelpers(object):
    """
    A set of utilities related to parsing URLs.
    """

    @classmethod
    def only_domain(cls, url):
        """Extracts only the domain part of the url, excluding the subdomain """
        try:
            ext = tldextract.extract(url)
        except TypeError as e:
            raise UserWarning("could not extract url {url} because of exception {e} ".format(
                url=url,
                e=e
            ))
        return '.'.join(
            part for part in [
                ext.domain,
                ext.suffix
            ] if part
        )

    @classmethod
    def no_dynamic(cls, url):
        """Removes the fragment, params and query part of the url"""
        parsed = urlsplit(url)
        return urlunsplit(
            parsed[:3] + ('', '')
        )

    @classmethod
    def within_domain(cls, url, domain):
        url_domain = cls.only_domain(url)
        return url_domain == domain

class TimeHelpers:
    """
    A set of utilities relating to time parsing.
    """

    safeTimeFormat = "%Y-%m-%d_%H-%M-%S"
    _override_time = None

    @classmethod
    def set_override_time(cls, time_struct=None):
        """ sets the override time to a local time struct or removes override """
        if time_struct:
            assert isinstance(time_struct, time.struct_time)
        cls._override_time = time_struct

    @classmethod
    def current_loctstruct(cls):
        """ returns the current local time as a time.struct_time or the
        struct_time that was set to override the curren time """
        if cls._override_time:
            return cls._override_time
        else:
            return time.gmtime()

    @classmethod
    def current_tsecs(cls):
        """ Returns the curren time in number of seconds since the epoch or the
        time that was set to override """
        if cls._override_time:
            return time.mktime(cls._override_time)
        else:
            return time.time()

    @classmethod
    def star_strp_mktime(cls, string, fmt=None):
        """
        Determine number of seconds since epoch given a formatted time string or datetime.

        Args:
            string (basestring):
            fmt (basestring): The format string.

        Returns:
            int: The number of seconds since epoch.
        """


        if fmt is None:
            fmt = cls.safeTimeFormat
        if string:
            if isinstance(string, datetime.datetime):
                # sometimes yaml does strings as datetime.datetime
                string.microsecond = 0
                string = str(string)
            string = unicode(string)
            tstruct = time.strptime(string, fmt)
            if tstruct:
                return time.mktime(tstruct)
        return 0

    @classmethod
    def safe_time_to_str(cls, secs, fmt=None):
        """
        Convert time to formatted local time string.

        Args:
            secs (Number, basestring): The number of seconds since epoch.
            fmt (basestring): The format string.

        Returns:
            str: formatted time string
        """

        if not fmt:
            fmt = cls.safeTimeFormat
        if secs:
            assert isinstance(secs, (Number, basestring)), \
                "param must be a number or string not %s" % type(secs)
            secs = float(secs)
            return time.strftime(fmt, time.localtime(secs))

    @classmethod
    def has_happened_yet(cls, secs):
        """
        Determine if a time has happened yet according to overrides.

        Args:
            secs (Number, basestring): The number of seconds since epoch.

        Returns:
            bool: Whether the time has happened yet according to overrides.
        """

        assert isinstance(secs, (Number, basestring)), \
            "secs param must be a number or string not %s" % type(secs)
        secs = float(secs)
        return secs >= cls.current_tsecs()

    @classmethod
    def get_safe_timestamp(cls, time_struct=None):
        """
        Get current MS friendly timestamp string.
        """

        if not time_struct:
            time_struct = cls.current_loctstruct()
        return time.strftime(cls.safeTimeFormat, time_struct)
