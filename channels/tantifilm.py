# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Tantifilm
# ------------------------------------------------------------

import re

from core import scrapertools, httptools, tmdb, support
from core.item import Item
from core.support import log
from platformcode import logger
from specials import autorenumber
from platformcode import config, unify
from lib.unshortenit import unshorten_only


def findhost():
    permUrl = httptools.downloadpage('https://www.tantifilm.info/', follow_redirects=False).data
    host = 'https://' + scrapertools.find_single_match(permUrl, r'Ora siamo ([A-Za-z0-9./]+)')
    return host

host = config.get_channel_url(findhost)
headers = [['Referer', host]]
list_servers = ['verystream', 'openload', 'streamango', 'vidlox', 'youtube']
list_quality = ['default']


@support.menu
def mainlist(item):
    log()

    top = [('Generi', ['', 'category'])]
    film = ['/film',
        ('Al Cinema', ['/watch-genre/al-cinema/']),
        ('HD', ['/watch-genre/altadefinizione/']),
        ('Sub-ITA', ['/watch-genre/sub-ita/'])

        ]

    tvshow = ['/serie-tv/',
        ('HD', ['/watch-genre/serie-altadefinizione/']),
        ('Miniserie', ['/watch-genre/miniserie-1/']),
        ('Programmi TV', ['/watch-genre/programmi-tv/']),
        #('LIVE', ['/watch-genre/live/'])
        ]

    anime = ['/watch-genre/anime/'
        ]

    search = ''
    return locals()

@support.scrape
def peliculas(item):
    log()


    if item.args == 'search':
        patron = r'<a href="(?P<url>[^"]+)" title="Permalink to\s(?P<title>[^"]+) \((?P<year>[^<]+)\).*?".*?<img[^s]+src="(?P<thumb>[^"]+)".*?<div class="calitate">\s*<p>(?P<quality>[^<]+)<\/p>'
        # support.regexDbg(item, patron, headers)
    else:
        patronNext = r'<a class="nextpostslink" rel="next" href="([^"]+)">'
        patron = r'<div class="mediaWrap mediaWrapAlt">\s?<a href="(?P<url>[^"]+)"(?:[^>]+>|)>?\s?<img[^s]+src="([^"]+)"[^>]+>\s?<\/a>[^>]+>[^>]+>[^>]+>(?P<title>.+?)(?:[ ]<lang>[sSuUbB\-iItTaA]+)?(?:[ ]?\((?P<year>[\-\d+]+)\)).[^<]+[^>]+><\/a>.+?<p>\s*(?P<quality>[a-zA-Z-0-9\.]+)\s*<\/p>[^>]+>'
        patronBlock = r'<div id="main_col">(?P<block>.*?)<!\-\- main_col \-\->'

    # if item.args != 'all' and item.args != 'search':
    #     action = 'findvideos' if item.extra == 'movie' else 'episodios'
    #     item.contentType = 'movie' if item.extra == 'movie' else 'tvshow'
    #debug = True
    return locals()


@support.scrape
def episodios(item):
    log()
    if not item.data:
        data_check = httptools.downloadpage(item.url, headers=headers).data
        data_check = re.sub('\n|\t', ' ', data_check)
        data_check = re.sub(r'>\s+<', '> <', data_check)
    else:
        data_check = item.data
    patron_check = r'<iframe src="([^"]+)" scrolling="no" frameborder="0" width="626" height="550" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true">'
    item.url = scrapertools.find_single_match(data_check, patron_check)

    patronBlock = r'Stagioni<\/a>.*?<ul class="nav navbar-nav">(?P<block>.*?)<\/ul>'
    patron = r'<a href="(?P<url>[^"]+)"\s*>\s*<i[^>]+><\/i>\s*(?P<episode>\d+)<\/a>'
    # debug = True

    otherLinks = support.match(data_check, patronBlock='<div class="content-left-film">.*?Keywords', patron='([0-9]+)(?:×|x)([0-9]+(?:-[0-9]+)?)(.*?)(?:<br|$)').matches

    def itemlistHook(itemlist):
        retItemlist = []
        for item in itemlist:
            item.contentType = 'episode'

            season = unify.remove_format(item.title)
            season_data = httptools.downloadpage(item.url).data
            season_data = re.sub('\n|\t', ' ', season_data)
            season_data = re.sub(r'>\s+<', '> <', season_data)
            block = scrapertools.find_single_match(season_data, 'Episodi.*?<ul class="nav navbar-nav">(.*?)</ul>')
            episodes = scrapertools.find_multiple_matches(block, '<a href="([^"]+)"\s*>\s*<i[^>]+><\/i>\s*(\d+)<\/a>')
            for url, episode in episodes:
                i = item.clone()
                i.action = 'findvideos'
                i.url = url
                i.contentSeason = str(season)
                i.contentEpisodeNumber = str(episode)
                i.title = str(season) + 'x' + str(episode)
                for ep in otherLinks:
                    if int(ep[0]) == int(season) and int(ep[1].split('-')[-1]) == int(episode):
                        i.otherLinks = ep[2]
                        break
                retItemlist.append(i)
        retItemlist.sort(key=lambda e: (int(e.contentSeason), int(e.contentEpisodeNumber)))
        return retItemlist

    #debug = True
    return locals()


@support.scrape
def category(item):
    blacklist = ['Serie TV Altadefinizione', 'HD AltaDefinizione', 'Al Cinema', 'Serie TV', 'Miniserie', 'Programmi Tv', 'Live', 'Trailers', 'Serie TV Aggiornate', 'Aggiornamenti', 'Featured']
    patron = '<li><a href="(?P<url>[^"]+)"><span></span>(?P<title>[^<]+)</a></li>'
    patron_block = '<ul class="table-list">(.*?)</ul>'
    action = 'peliculas'

    return locals()


def search(item, texto):
    log(texto)


    item.url = host + "/?s=" + texto
    try:
        item.args = 'search'
        return peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


@support.scrape
def newest(categoria):
    if categoria == 'series':
        item = Item(url=host + '/aggiornamenti-giornalieri-serie-tv-2')
        item.contentType = 'tvshow'
        patronBlock = 'Aggiornamenti Giornalieri Serie TV.*?<div class="sp-body folded">(?P<block>.*?)</div>'
        patron = '<p>(?P<title>.*?)\((?P<year>[0-9]{4})-?\)\s*streaming.*?href="(?P<url>[^"]+)'

        def itemHook(item):
            item.title = item.contentTitle = item.fulltitle = item.contentSerieName = item.contentTitle = scrapertools.htmlclean(item.title)
            return item

    return locals()


def findvideos(item):
    log()
    listurl = set()
    itemlist = []
    support.log("ITEMLIST: ", item)
    data = support.match(item.url, headers=headers).data
    check = support.match(data, patron=r'<div class="category-film">(.*?)</div>').match
    if 'sub' in check.lower():
        item.contentLanguage = 'Sub-ITA'
    support.log("CHECK : ", check)
    if 'anime' in check.lower():
        item.contentType = 'tvshow'
        item.data = data
        support.log('select = ### è una anime ###')
        try:
            return episodios(item)
        except:
            pass
    elif 'serie' in check.lower():
        item.contentType = 'tvshow'
        item.data = data
        return episodios(item)

    if 'protectlink' in data:
        urls = scrapertools.find_multiple_matches(data, r'<iframe src="[^=]+=(.*?)"')
        support.log("SONO QUI: ", urls)
        for url in urls:
            url = url.decode('base64')
            # tiro via l'ultimo carattere perchè non c'entra
            url, c = unshorten_only(url)
            if 'nodmca' in url:
                page = httptools.downloadpage(url, headers=headers).data
                url = '\t' + scrapertools.find_single_match(page, '<meta name="og:url" content="([^=]+)">')
            if url:
                listurl.add(url)
    data += '\n'.join(listurl)

    itemlist = support.server(item, data + item.otherLinks, patronTag='Keywords:\s*<span>([^<]+)')
    return itemlist
