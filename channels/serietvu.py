# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per serietvu.py
# ----------------------------------------------------------

"""
    La pagina novità contiene al max 25 titoli
"""
import re

from core import support, httptools, scrapertools
from core.item import Item
from core.support import log
from platformcode import config

host = config.get_channel_url()
headers = [['Referer', host]]

list_servers = ['speedvideo']
list_quality = ['default']


@support.menu
def mainlist(item):

    tvshow = ['/category/serie-tv',
              ('Ultimi episodi', ['/ultimi-episodi/', 'peliculas', 'update']),
              ('Generi', ['', 'genres', 'genres'])
    ]

    return locals()


@support.scrape
def peliculas(item):
    patronBlock = r'<div class="wrap">\s*<h.>.*?</h.>(?P<block>.*?)<footer>'

    if item.args != 'update':
        action = 'episodios'
        patron = r'<div class="item">\s*<a href="(?P<url>[^"]+)" data-original="(?P<thumb>[^"]+)" class="lazy inner">[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)<'
    else:
        action = 'findvideos'
        patron = r'<div class="item">\s+?<a href="(?P<url>[^"]+)"\s+?data-original="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)<[^>]+>\((?P<episode>[\dx\-]+)\s+?(?P<lang>Sub-Ita|[iITtAa]+)\)<'
        pagination = 25

    patronNext = r'<li><a href="([^"]+)"\s+?>Pagina successiva'
    return locals()


@support.scrape
def episodios(item):
    seasons = support.match(item, patron=r'<option value="(\d+)"[^>]*>\D+(\d+)').matches
    patronBlock = r'</select><div style="clear:both"></div></h2>(?P<block>.*?)<div id="trailer" class="tab">'
    patron = r'(?:<div class="list (?:active)?")?\s*<a data-id="\d+(?:[ ](?P<lang>[SuUbBiItTaA\-]+))?"(?P<other>[^>]+)>.*?Episodio [0-9]+\s?(?:<br>(?P<title>[^<]+))?.*?Stagione (?P<season>[0-9]+) , Episodio - (?P<episode>[0-9]+).*?<(?P<url>.*?<iframe)'
    def itemHook(item):
        for value, season in seasons:
            log(value)
            log(season)
            item.title = item.title.replace(value+'x',season+'x')
        item.url += '\n' + item.other
        return item
    return locals()


@support.scrape
def genres(item):
    blacklist = ["Home Page", "Calendario Aggiornamenti"]
    action = 'peliculas'
    patronBlock = r'<h2>Sfoglia</h2>\s*<ul>(?P<block>.*?)</ul>\s*</section>'
    patronMenu = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a></li>'
    return locals()


def search(item, text):
    log(text)
    item.url = host + "/?s=" + text
    try:
        item.contentType = 'tvshow'
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            log("%s" % line)
        return []


def newest(categoria):
    log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = host + "/ultimi-episodi"
            item.action = "peliculas"
            item.contentType = 'tvshow'
            item.args = 'update'
            itemlist = peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            log("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    log()
    if item.args != 'update':
        data = item.url
        return support.server(item, data=data)
    else:
        itemlist = []
        item.infoLabels['mediatype'] = 'episode'

        data = httptools.downloadpage(item.url, headers=headers).data
        data = re.sub('\n|\t', ' ', data)
        data = re.sub(r'>\s+<', '> <', data)
        url_video = scrapertools.find_single_match(data, r'<div class="item"> <a data-id="[^"]+" data-href="([^"]+)" data-original="[^"]+"[^>]+> <div> <div class="title">Episodio \d+', -1)
        url_serie = scrapertools.find_single_match(data, r'<link rel="canonical" href="([^"]+)"\s?/>')
        goseries = support.typo(">> Vai alla Serie:", ' bold')
        series = support.typo(item.contentSerieName, ' bold color kod')

        itemlist = support.server(item, data=url_video)

        itemlist.append(
            Item(channel=item.channel,
                 title=goseries + series,
                 fulltitle=item.fulltitle,
                 show=item.show,
                 contentType='tvshow',
                 contentSerieName=item.contentSerieName,
                 url=url_serie,
                 action='episodios',
                 contentTitle=item.contentSerieName,
                 plot = goseries + series + "con tutte le puntate",
                 thumbnail = support.thumb(thumb='tvshow.png')
                ))

        return itemlist
