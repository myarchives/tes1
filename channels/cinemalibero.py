# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'cinemaLibero'
# ------------------------------------------------------------

import re

from core import httptools, support, scrapertools
from core.item import Item
from platformcode import config

list_servers = ['akstream', 'wstream', 'backin', 'clipwatching', 'cloudvideo', 'verystream', 'onlystream', 'mixdrop']
list_quality = ['default']

# rimanda a .today che contiene tutti link a .plus
# def findhost():
#     permUrl = httptools.downloadpage('https://www.cinemalibero.online/', follow_redirects=False).headers
#     try:
#         import urlparse
#     except:
#         import urllib.parse as urlparse
#     p = list(urlparse.urlparse(permUrl['location'].replace('https://www.google.com/search?q=site:', '')))
#     if not p[0]:
#         p[0] = 'https'
#     return urlparse.urlunparse(p)

host = config.get_channel_url()
headers = [['Referer', host]]

@support.menu
def mainlist(item):

    film = ['/category/film/',
            ('Novità', ['', 'peliculas', 'update']),
            ('Generi', ['', 'genres'])]

    tvshow = ['/category/serie-tv/']

    anime = ['/category/anime-giapponesi/']

##    Sport = [(support.typo('Sport', 'bullet bold'), ['/category/sport/', 'peliculas', 'sport', 'tvshow'])]
    news = [('Ultimi episodi Serie/Anime', ['/aggiornamenti-serie-tv/', 'peliculas', 'update', 'tvshow'])]

    search = ''

    return locals()


@support.scrape
def peliculas(item):
    action = 'check'
    patronBlock = r'<div class="container">.*?class="col-md-12[^"]*?">(?P<block>.*?)<div class=(?:"container"|"bg-dark ")>'
    if item.args == 'newest':
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>(?P<title>[^<]+)<[^>]+>[^>]+>(?:[^>]+>)?\s?(?P<rating>[\d\.]+)?[^>]+>.+?(?:[ ]\((?P<year>\d{4})\))?<[^>]+>[^>]+>(.?[\d\-x]+\s\(?(?P<lang>[sSuUbBiItTaA\-]+)?\)?\s?(?P<quality>[\w]+)?[|]?\s?(?:[fFiInNeE]+)?\s?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?)?'
        pagination = 25
    elif item.contentType == 'movie':
        patron = r'<a href="(?P<url>[^"]+)" title="(?P<title>.+?)(?:[ ]\[(?P<lang>[sSuUbB\-iItTaA]+)\])?(?:[ ]\((?P<year>\d{4})\))?"\s*alt="[^"]+"\s*class="[^"]+"(?: style="background-image: url\((?P<thumb>.+?)\)">)?\s*<div class="voto">[^>]+>[^>]+>.(?P<rating>[\d\.a-zA-Z\/]+)?[^>]+>[^>]+>[^>]+>(?:<div class="genere">(?P<quality>[^<]+)</div>)?'
        if item.args == 'update':
            patronBlock = r'<section id="slider">(?P<block>.*?)</section>'
            patron = r'<a href="(?P<url>(?:https:\/\/.+?\/(?P<title>[^\/]+[a-zA-Z0-9\-]+)(?P<year>\d{4})))/".+?url\((?P<thumb>[^\)]+)\)">'
    elif item.contentType == 'tvshow':
        if item.args == 'update':
            patron = r'<a href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">\s<div class="titolo">(?P<title>.+?)(?: &#8211; Serie TV)?(?:\([sSuUbBiItTaA\-]+\))?[ ]?(?P<year>\d{4})?</div>[ ]<div class="genere">(?:[\w]+?\.?\s?[\s|S]?[\dx\-S]+?\s\(?(?P<lang>[iItTaA]+|[sSuUbBiItTaA\-]+)\)?\s?(?P<quality>[HD]+)?|.+?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?</div>)'
            pagination = 25
        else:
            patron = r'<a href="(?P<url>[^"]+)"\s*title="(?P<title>[^"\(]+)(?:"|\()(?:(?P<year>\d+)[^"]+)?.*?url\((?P<thumb>[^\)]+)\)(?:.*?<div class="voto">[^>]+>[^>]+>\s*(?P<rating>[^<]+))?.*?<div class="titolo">[^>]+>(?:<div class="genere">[^ ]*(?:\s\d+)?\s*(?:\()?(?P<lang>[^\)< ]+))?'
    else:
        #search
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>[^>]+>[^>]+>(?:[^>]+>)?\s?(?P<rating>[\d\.]+)?[^>]+>(?P<title>.+?)(?:[ ]\((?P<year>\d{4})\))?<[^>]+>[^>]+>(.?[\d\-x]+\s\(?(?P<lang>[sSuUbBiItTaA\-]+)?\)?\s?(?P<quality>[\w]+)?[|]?\s?(?:[fFiInNeE]+)?\s?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?)?'

    def itemHook(item):
        if 'sub' in item.contentLanguage.lower() and not 'ita' in item.contentLanguage.lower():
            item.contentLanguage= 'Sub-ITA'
            item.title = re.sub('[Ss]ub(?:-)?', item.contentLanguage, item.title)
        if item.lang2:
            if len(item.lang2)<3:
                item.lang2 = 'ITA'
            item.contentLanguage = item.lang2
            item.title += support.typo(item.lang2, '_ [] color kod')
        if item.args == 'update':
            item.title = item.title.replace('-', ' ')

        return item

    patronNext = r'<a class="next page-numbers".*?href="([^"]+)">'
    return locals()

@support.scrape
def episodios(item):
    data=item.data
    # debug=True
    if item.args == 'anime':
        support.log("Anime :", item)
        # blacklist = ['Clipwatching', 'Verystream', 'Easybytez', 'Flix555', 'Cloudvideo']
        patron = r'<a target=(?P<url>[^>]+>(?P<title>Episodio\s(?P<episode>\d+))(?::)?(?:(?P<title2>[^<]+))?.*?(?:<br|</p))'
        patronBlock = r'(?:Stagione (?P<season>\d+))?(?:</span><br />|</span></p>|strong></p>)(?P<block>.*?)(?:<div style="margin-left|<span class="txt_dow">)'
        item.contentType = 'tvshow'
    else:# item.extra == 'serie':
        support.log("Serie :", item)
        patron = r'(?P<episode>\d+(?:&#215;|×)?\d+\-\d+|\d+(?:&#215;|×)\d+)[;]?[ ]?(?:(?P<title>[^<]+)(?P<url>.*?)|(\2[ ])(?:<(\3.*?)))(?:</a><br />|</a></p>|$)'
        patronBlock = r'<p><strong>(?:.+?[Ss]tagione\s)?(?:(?P<lang>iTA|ITA|Sub-ITA|Sub-iTA))?.*?</strong>(?P<block>.+?)(?:</span|</p)'
        item.contentType = 'tvshow'
    def itemHook(item):
        if not scrapertools.find_single_match(item.title, r'(\d+x\d+)'):
            item.title = re.sub(r'(\d+) -', '1x\\1', item.title)
        return item

    return locals()


@support.scrape
def genres(item):

    action='peliculas'
    patron_block=r'<div id="bordobar" class="dropdown-menu(?P<block>.*?)</li>'
    patronMenu=r'<a class="dropdown-item" href="(?P<url>[^"]+)" title="(?P<title>[A-z]+)"'

    return locals()


def search(item, texto):
    support.log(item.url,texto)
    text = texto.replace(' ', '+')
    item.url = host + "/?s=" + texto
    item.contentType = 'tv'
    item.args = 'search'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log("%s" % line)
    return []

def newest(categoria):
    support.log('newest ->', categoria)
    itemlist = []
    item = Item()
    item.args = 'newest'
    try:
        if categoria == 'peliculas':
            item.url = host+'/category/film/'
            item.contentType = 'movie'
        elif categoria == 'series' or categoria == 'anime':
            item.args = 'update'
            item.url = host+'/aggiornamenti-serie-tv/'
            item.contentType = 'tvshow'
        item.action = 'peliculas'
        itemlist = peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            support.log('newest log: ', (line))
        return []

    return itemlist

def check(item):
    support.log()
    data = support.match(item.url, headers=headers).data
    if data:
        blockAnime = support.match(data, patron=r'<div id="container" class="container">(.+?<div style="margin-left)').match

        if support.match(blockAnime, patron=r'\d+(?:&#215;|×)?\d+\-\d+|\d+(?:&#215;|×)\d+').match:
            item.contentType = 'tvshow'
            item.data = data
            return episodios(item)

        elif blockAnime and ('episodio' in blockAnime.lower() or 'saga' in blockAnime.lower()):
            item.contentType = 'tvshow'
            item.args = 'anime'
            item.data = blockAnime
            return episodios(item)

        else:
            item.contentType = 'movie'
            item.url = data
            return findvideos(item)

def findvideos(item):
    support.log()
    item.url = item.url.replace('http://rapidcrypt.net/verys/', '').replace('http://rapidcrypt.net/open/', '') #blocca la ricerca
    return support.server(item, data= item.url)
