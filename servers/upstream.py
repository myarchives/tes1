# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector UP Stream By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
	logger.info("(page_url='%s')" % page_url)
	global data
	data = httptools.downloadpage(page_url).data
	if "<h2>WE ARE SORRY</h2>" in data or '<title>404 Not Found</title>' in data:
		return False, config.get_localized_string(70449) % "UPstream"
	return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
	video_urls = []
	media_url = scrapertools.find_single_match(data, r'file:"([^"]+)"')
	video_urls.append(["%s [UPstream]" % media_url.split('.')[-1], media_url])

	return video_urls
