# -*- coding: utf-8 -*-
# Kodi on Demand - Kodi Addon - Kodi Addon
# by DrZ3r0 - Fix Alhaziel

import json
import re

try:
    import urllib.parse as urllib
except ImportError:
    import urllib

from core import httptools, scrapertools
from platformcode import logger, config, platformtools

headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0']]

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    resp = httptools.downloadpage(page_url)

    global data, real_url
    data = resp.data

    page_url = resp.url
    if '/streaming.php' in page_url in page_url:
        code = httptools.downloadpage(page_url, headers=headers, follow_redirects=False, only_headers=True).headers['location'].split('/')[-1].replace('.html', '')
        # logger.info('WCODE=' + code)
        page_url = 'https://wstream.video/video.php?file_code=' + code
        data = httptools.downloadpage(page_url, headers=headers, follow_redirects=True).data

    real_url = page_url
    if "Not Found" in data or "File was deleted" in data:
        return False, config.get_localized_string(70449) % 'Wstream'
    else:
        return True, ""


# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    def int_bckup_method():
        global data,headers
        page_url = scrapertools.find_single_match(data, r"""<center><a href='(https?:\/\/wstream[^']+)'\s*title='bkg'""")
        if page_url:
            data = httptools.downloadpage(page_url, headers=headers, follow_redirects=True, post={'g-recaptcha-response': captcha}).data

    def getSources(data):
        possibileSources = scrapertools.find_multiple_matches(data, r'sources:\s*(\[[^\]]+\])')
        for data in possibileSources:
            try:
                data = re.sub('([A-z]+):(?!/)', '"\\1":', data)
                keys = json.loads(data)

                for key in keys:
                    video_urls.append(['%s [%sp]' % (key['type'].replace('video/', ''), key['label']),
                                       key['src'].replace('https', 'http') + '|' + _headers])
            except:
                pass

    logger.info("[Wstream] url=" + page_url)
    video_urls = []
    global data, real_url
    # logger.info(data)
    sitekey = scrapertools.find_multiple_matches(data, """data-sitekey=['"] *([^"']+)""")
    if sitekey: sitekey = sitekey[-1]
    captcha = platformtools.show_recaptcha(sitekey, page_url) if sitekey else ''

    possibleParam = scrapertools.find_multiple_matches(data,r"""<input.*?(?:name=["']([^'"]+).*?value=["']([^'"]*)['"]>|>)""")
    if possibleParam and possibleParam[0]:
        post = {param[0]: param[1] for param in possibleParam if param[0]}
        if captcha: post['g-recaptcha-response'] = captcha
        if post:
            data = httptools.downloadpage(real_url, headers=headers, post=post, follow_redirects=True).data
        elif captcha:
            int_bckup_method()
    elif captcha:
        int_bckup_method()
    else:
        platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(707434))
        return []

    headers.append(['Referer', real_url])
    _headers = urllib.urlencode(dict(headers))

    post_data = scrapertools.find_single_match(data, r"</div>\s*<script type='text/javascript'>(eval.function.p,a,c,k,e,.*?)\s*</script>")
    if post_data != "":
        from lib import jsunpack
        data = jsunpack.unpack(post_data)
        getSources(data)
    else:
        getSources(data)

    if not video_urls:
        media_urls = scrapertools.find_multiple_matches(data, r'(http[^\s]*?\.mp4)')

        for media_url in media_urls:
            video_urls.append(['video' + " mp4 [wstream] ", media_url + '|' + _headers])
    video_urls.sort(key=lambda x: x[0])
    return video_urls
