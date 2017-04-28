# -*- coding: utf-8 -*-
"""
Scrapy Pipelines for dealing with scraped metrics.
"""

import json

class JsonWriterPipeline(object):
    """Basic pipeline which dumps items to a .jl file."""

    def __init__(self, *args, **kwargs):
        super(JsonWriterPipeline, self).__init__(*args, **kwargs)
        self.file = None

    def open_spider(self, _):
        self.file = open('items.jl', 'wb')

    def close_spider(self, _):
        self.file.close()

    def process_item(self, item, _):
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item
