# -*- coding: utf-8 -*-
"""
Collection of spiders for scraping popularity metrics.
"""

import sys
import os

import scrapy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import scrapop
from scrapop.utils import TimeHelpers

class PopMetric(scrapy.Item):
    """A value of a given metric at a particular time."""

    value = scrapy.Field()
    name = scrapy.Field()
    tsecs = scrapy.Field()

class PopSpider(scrapy.Spider):
    """Abstract popularity metric spider."""

    name = "popularity"

    def __init__(self, *args, **kwargs):
        super(PopSpider, self).__init__(*args, **kwargs)

        if hasattr(self, 'start_url'):
            start_url = getattr(self, 'start_url')
            if start_url:
                self.start_urls.append(start_url)

    def parse(self, response):
        self.log('parsing: {response}'.format(response=response))

        metric_value = None
        if hasattr(self, 'metric_xpath'):
            selector = getattr(self, 'metric_xpath')
            if selector:
                metric_value = response.xpath(selector).extract_first()
        elif hasattr(self, 'metric_css'):
            selector = getattr(self, 'metric_css')
            if selector:
                metric_value = response.css(selector).extract_first()
        else:
            self.log('No selector found')
            return

        if metric_value is None:
            self.log('no metric_value found')
            return

        return PopMetric(
            name=self.name,
            value=metric_value,
            tsecs=TimeHelpers.current_tsecs(),
        )



class AlexaSpider(PopSpider):
    """Spider for Alexa-like popularity metrics."""

    name = "alexa"
    metric_css = "section#traffic-rank-content strong.metrics-data"

    def __init__(self, *args, **kwargs):
        super(AlexaSpider, self).__init__(*args, **kwargs)
