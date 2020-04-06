# -*- coding: utf-8 -*-

import time
import urllib

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data or "File Does not Exist" in data:
        return False, config.get_localized_string(70449) % "Turbovid"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password="", server='Turbovid'):

    logger.info("(turbovid page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = data.replace('"', "'")
    page_url_post = scrapertools.find_single_match(data, "<Form method='POST' action='([^']+)'>")
    imhuman = "&imhuman=" + scrapertools.find_single_match(data, "name='imhuman' value='([^']+)'").replace(" ", "+")
    post = urllib.urlencode({k: v for k, v in scrapertools.find_multiple_matches(data, "name='([^']+)' value='([^']*)'")}) + imhuman

    time.sleep(6)
    data = httptools.downloadpage(page_url_post, post=post).data
    logger.info("(data page_url='%s')" % data)
    sources = scrapertools.find_single_match(data, r'sources: \[([^\]]+)\]')

    for media_url in scrapertools.find_multiple_matches(sources, '"([^"]+)"'):
        ext = scrapertools.get_filename_from_url(media_url)[-4:]
        video_urls.append(["%s [%s]" % (ext, server), media_url])
    return video_urls
