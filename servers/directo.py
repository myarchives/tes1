# -*- coding: utf-8 -*-

from platformcode import logger, config


# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    video_urls = [["%s %s" % (page_url[-4:], config.get_localized_string(30137)), page_url]]

    return video_urls
