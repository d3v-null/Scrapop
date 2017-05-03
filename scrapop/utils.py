# -*- coding: utf-8 -*-
"""
Utilities for Scrapop module.
"""

from __future__ import print_function
import time
import datetime
import os
import re
from numbers import Number
from urlparse import urlsplit, urlunsplit

import httplib2
from apiclient import discovery
from oauth2client import client as oauth2_client
from oauth2client import tools
from oauth2client.file import Storage
import tldextract
from awis import AwisApi
#pylint: disable=no-name-in-module
from lxml.etree import tostring as etree_tostring
from lxml.etree import ElementTree


class SanitationUtils(object):
    """
    A set of utilities related to sanitizing strings.
    """

    re_gss_hyperlink = r'=HYPERLINK\("(?P<href>[^"]*)",\s*"(?P<text>[^"]*)"\)'
    re_alexa_siteinfo_url = (r'http://www\.alexa\.com/siteinfo/'
                             r'(?P<domain>[^\s\#]+)(\#(?P<id>\S*))?')

    @classmethod
    def to_ascii(cls, thing):
        """
        Convert the parameter to an ascii string.
        """
        if not isinstance(basestring, thing):
            thing = unicode(thing, errors='backslashreplace')
        return thing.encode(errors='backslashreplace')



    @classmethod
    def extract_target_gss_cell(cls, cell):
        """
        Extract the target domain from google sheet cell.
        """
        if not cell:
            return
        target_match = re.match(cls.re_gss_hyperlink, cell)
        if target_match:
            href = target_match.groupdict().get('href')
            href_match = re.match(cls.re_alexa_siteinfo_url, href)
            if href_match:
                domain = href_match.groupdict().get('domain')
                return domain

            text = target_match.groupdict().get('text')
            for token in text.split():
                extracted_hostname = UrlUtils.extract_hostname(token)
                if extracted_hostname:
                    return extracted_hostname
        for token in cell.split():
            extracted_hostname = UrlUtils.extract_hostname(token)
            if extracted_hostname:
                return extracted_hostname

class UrlUtils(object):
    """
    A set of general utilities related to parsing URLs.
    """

    re_domain = r'[\w.~-]\.[\w.~-]'

    @classmethod
    def extract_hostname(cls, token):
        """
        Extract the hostname from a string-like token.
        """

        match = re.match(cls.re_domain, token)
        if match:
            return match.group(0)

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

class ListUtils(object):
    """
    Utilities related to list comprehension.
    """

    @classmethod
    def get_firsts(cls, superlist):
        """
        Get the first item of each sublist in the superlist.
        """

        return [
            sublist[0] if len(sublist) else None \
            for sublist in superlist
        ]

    @classmethod
    def unique_true(cls, seq):
        """
        Get list of members that are truthy from a sequence of hashables.
        """

        return list(set(seq))

class GssUtils(object):
    """
    Utilities related to Google Drive Spreadsheets API.
    """

    @classmethod
    def get_credentials(cls, options):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'sheets.googleapis.com-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = oauth2_client.flow_from_clientsecrets(options.client_secret_file, options.scopes)
            flow.user_agent = options.app_name
            credentials = tools.run_flow(flow, store, options)
            print('Storing credentials to ' + credential_path)
        return credentials

    @classmethod
    def get_range(cls, spreadsheet_id, range_name, value_render, options):
        """Get column from spreadsheet."""
        credentials = cls.get_credentials(options)
        http = credentials.authorize(httplib2.Http())
        discovery_url = ('https://sheets.googleapis.com/$discovery/rest?'
                         'version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discovery_url)

        request_arguments = dict(
            spreadsheetId=spreadsheet_id,
            range=range_name,
        )
        if value_render:
            request_arguments.update(valueRenderOption=value_render)

        #pylint: disable=no-member
        result = service.spreadsheets().values().get(**request_arguments).execute()
        values = result.get('values', [])

        return values

class AwisUtils(object):
    """
    Utilities related to AWIS API.
    """

    @classmethod
    def get_metrics(cls, domains, metrics, options):
        awis_client = AwisApi(options.key_id, options.secret_key)

        tree = awis_client.url_info(domains, *metrics)

        alexa_prefix = awis_client.NS_PREFIXES['alexa']
        awis_prefix = awis_client.NS_PREFIXES['awis']

        elem = tree.find('//{%s}StatusCode' % alexa_prefix)
        if elem.text != 'Success':
            raise UserWarning('unable to get metrics: %s' % etree_tostring(tree))

        metric_values = []
        for elem_result in tree.findall('//{%s}UrlInfoResult' % awis_prefix):
            # print("UrlInfoResult Elem: %s" % etree_tostring(elem_result))
            # print("elem_result tag: %s, text: %s" % (elem_result.tag, elem_result.text))
            tree_result = ElementTree(elem_result)
            domain = None
            elem_url = tree_result.find('//{%s}DataUrl' % awis_prefix)
            if elem_url is not None:
                # print("elem_url tag: %s, text: %s" % (elem_url.tag, elem_url.text))
                domain = elem_url.text
                if domain[-1] == "/":
                    domain = domain[:-1]
            # if domain:
                # print("getting results for domain %s" % domain)

            domain_metrics = {}
            for metric in metrics:
                elem_metric = tree_result.find('//{%s}%s' % (awis_prefix, metric))
                if elem_metric is None:
                    raise UserWarning('unable to find metric within UrlInfoResult: %s' \
                        % etree_tostring(tree_result))
                domain_metrics[metric] = elem_metric.text
            metric_values.append(domain_metrics)

        print("success: %s" % metric_values)
        return metric_values
