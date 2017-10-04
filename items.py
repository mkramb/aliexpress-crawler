# -*- coding: utf-8 -*-

from scrapy.item import Item, Field


class ProductItem(Item):
    name = Field()
    url = Field()
    orders = Field()
    category = Field()
    subcategory = Field()
    store = Field()
    feedback = Field()
