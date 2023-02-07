import json
import time

from operator import itemgetter
from seoanalyzer.website import Website

def analyze(url, sitemap_url=None, analyze_extra_tags=False, follow_links=True):
    start_time = time.time()

    def calc_total_time():
        return time.time() - start_time

    output = {'pages': [], 'keywords': [], 'errors': [], 'total_time': calc_total_time()}

    site = Website(url, sitemap_url)
    site.crawl()

    for p in site.crawled_pages:
        output['pages'].append(p.talk())

    output['duplicate_pages'] = [list(site.content_hashes[p]) for p in site.content_hashes if len(site.content_hashes[p]) > 1]
    output['keywords'] = []
    output['total_time'] = calc_total_time()

    return output
