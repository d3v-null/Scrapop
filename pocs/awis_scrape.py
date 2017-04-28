# -*- coding: utf-8 -*-
"""scrapes rank from Alexa."""

from collections import OrderedDict
import scrapy
from scrapy.crawler import CrawlerProcess
import configargparse
import argparse

from spiders import metrics as metric_spiders

METRIC_SPIDERS = OrderedDict([
    ('alexa', metric_spiders.AlexaSpider),
])


def main():
    """Main function for scraping a single metric from a url."""

    argparser = configargparse.ArgumentParser(
        description="Scrape and store popularity metrics"
    )

    argparser.add_argument(
        '--spider-name',
        choices=METRIC_SPIDERS.keys(),
        default=METRIC_SPIDERS.keys()[0]
    )

    argparser.add_argument('--url', required=True)

    argparser.add_argument('--spider-args', help=argparse.SUPPRESS)

    spider_name = None
    crawl_url = None
    spider_args = None
    crawler_settings = None

    args = argparser.parse_args()
    if args:
        if args.spider_name:
            spider_name = args.spider_name
        if args.url:
            crawl_url = args.url

    scrape_metric(crawl_url, spider_name, spider_args, crawler_settings)


def scrape_metric(url, spider_name=None, spider_args=None, crawler_settings=None):
    """Scraping a single metric from a url."""

    spider_args = {
        'start_url':url
    }
    crawler_settings = {
        'ITEM_PIPELINES':{
            'scrapop.pipelines.JsonWriterPipeline': 100
        }
    }
    spider_class = METRIC_SPIDERS.values()[0]
    if spider_name is not None:
        spider_class = METRIC_SPIDERS[spider_name]

    process = CrawlerProcess(crawler_settings)
    process.crawl(spider_class, **spider_args)
    process.start()


if __name__ == '__main__':
    main()
