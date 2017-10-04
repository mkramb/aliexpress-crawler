# -*- coding: utf-8 -*-

from scrapy import Spider
from scrapy.http import Request
from urllib.parse import urlparse
from w3lib.url import add_or_replace_parameter, url_query_cleaner
from crawler.items import ProductItem

SORT_BY_ORDERS_KEY = 'SortType'
SORT_BY_ORDERS_VALUE = 'total_tranpro_desc'

SHOW_AS_LIST_KEY = 'g'
SHOW_AS_LIST_VALUE = 'y'

SITE_PROTOCOL = 'https:'
SITE_CATEGORIES_URL = '{0}//www.aliexpress.com/af/category/{1}.html'


def get_valid_url(url):
    if not urlparse(url).scheme:
        url = SITE_PROTOCOL + url
    return url_query_cleaner(url)


class AliExpressSpider(Spider):
    name = 'aliexpress'
    allowed_domains = ['aliexpress.com']
    start_urls = (
        'https://www.aliexpress.com/all-wholesale-products.html',
    )

    def parse(self, response):
        categories = response.css('.item .big-title a')

        for category in categories:
            url = SITE_CATEGORIES_URL.format(
                SITE_PROTOCOL,  category.css('::attr(href)').re_first(r'.*/category/(\d+)/.*')
            )

            yield Request(url, callback=self.parse_subcategory, meta={
                'category': {
                    'name': category.css('::text').extract_first(),
                    'url': url
                }
            })

    def parse_subcategory(self, response):
        subcategories = response.css('.bc-list .bc-cate-name a')

        if not subcategories:
            subcategories = response.css('.son-category li a')

        for subcategory in subcategories:
            url = get_valid_url(subcategory.css('::attr(href)').extract_first())

            request_url = add_or_replace_parameter(url, SORT_BY_ORDERS_KEY, SORT_BY_ORDERS_VALUE)
            request_url = add_or_replace_parameter(request_url, SHOW_AS_LIST_KEY, SHOW_AS_LIST_VALUE)

            yield Request(request_url, callback=self.parse_products, meta={
                'category': response.request.meta['category'],
                'subcategory': {
                    'name': subcategory.css('::text').extract_first(),
                    'url': url
                }
            })

    def parse_products(self, response):
        products = response.css('.son-list .item')

        for product in products:
            item = ProductItem()

            item.update({ 'category': response.request.meta['category'] })
            item.update({ 'subcategory': response.request.meta['subcategory'] })

            info = product.css('.product')
            history = product.css('.rate-history')
            score = product.css('.score-icon')
            store = product.css('.store-name')

            item['name'] = info.css('::text').extract_first()
            item['url'] = get_valid_url(info.css('::attr(href)').extract_first())
            item['orders'] = history.css('.order-num em::text').re_first(r'.*\((.*)\).*')

            item['store'] = {
                'name': store.css('a::text').extract_first(),
                'url': get_valid_url(store.css('a::attr(href)').extract_first())
            }

            item['feedback'] = {
                'score': score.css('::attr(feedbackscore)').extract_first(),
                'positive_percentage': score.css('::attr(sellerpositivefeedbackpercentage)').extract_first()
            }

            yield item
