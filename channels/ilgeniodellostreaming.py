# -*- coding: utf-8 -*-
# ------------------------------------------------------------
#
# Canale per ilgeniodellostreaming
# ------------------------------------------------------------


import re

from core import scrapertools, httptools, support
from core.support import log
from core.item import Item
from platformcode import config

host = config.get_channel_url()

list_servers = ['verystream', 'openload', 'streamango']
list_quality = ['default']

headers = [['Referer', host]]

@support.menu
def mainlist(item):
    support.log(item)

    film = ['/film/',
        ('Generi',['', 'genres', 'genres']),
        ('Per Lettera',['/film-a-z/', 'genres', 'letter']),
        ('Anni',['', 'genres', 'year']),
        ('Popolari',['/trending/?get=movies', 'peliculas', 'populared']),
        ('Più Votati', ['/ratings/?get=movies', 'peliculas', 'populared'])
        ]

    tvshow = ['/serie/',
        ('Aggiornamenti', ['/aggiornamenti-serie/', 'peliculas', 'update']),
        ('Popolari',['/trending/?get=tv', 'peliculas', 'populared']),
        ('Più Votati', ['/ratings/?get=tv', 'peliculas', 'populared'])

        ]

    anime = ['/anime/'
        ]

    Tvshow = [
        ('Show TV bullet bold', ['/tv-show/', 'peliculas', '', 'tvshow'])
        ]

    search = ''

    return locals()


@support.scrape
def peliculas(item):
    log()

    if item.args == 'search':
        patronBlock = r'<div class="search-page">(?P<block>.*?)<footer class="main">'
        patron = r'<img src="(?P<thumb>[^"]+)" alt="[^"]+" />[^>]+>(?P<type>[^<]+)</span>.*?<a href="(?P<url>[^"]+)">(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?</a>[^>]+>[^>]+>(?:<span class="rating">IMDb\s*(?P<rating>[^>]+)</span>)?.?(?:<span class="year">(?P<year>[0-9]+)</span>)?[^>]+>[^>]+><p>(?P<plot>.*?)</p>'

        typeContentDict={'movie': ['film'], 'tvshow': ['tv']}
        typeActionDict={'findvideos': ['film'], 'episodios': ['tv']}
    else:

        if item.contentType == 'movie':
            endBlock = '</article></div>'
        else:
            endBlock = '<footer class="main">'

        patronBlock = r'<header><h1>.+?</h1>(?P<block>.*?)'+endBlock

        if item.contentType == 'movie':
            if item.args == 'letter':
                patronBlock = r'<table class="table table-striped">(?P<block>.+?)</table>'
                patron = r'<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+><td class="mlnh-2"><a href="(?P<url>[^"]+)">(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?<[^>]+>[^>]+>[^>]+>(?P<year>\d{4})\s+<'
            elif item.args == 'populared':
                patron = r'<img src="(?P<thumb>[^"]+)" alt="[^"]+">[^>]+>[^>]+>[^>]+>[^>]+>\s+?(?P<rating>\d+.?\d+|\d+)<[^>]+>[^>]+>(?P<quality>[a-zA-Z\-]+)[^>]+>[^>]+>[^>]+>[^>]+><a href="(?P<url>[^"]+)">(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>(?P<year>\d+)<'
            else:

                #patron = r'<div class="poster">\s*<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)" alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+>\s*(?P<rating>[0-9.]+)<\/div><span class="quality">(?:SUB-ITA|)?(?P<quality>|[^<]+)?<\/span>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?<\/a>[^>]+>[^>]+>(?P<year>[^<]+)<\/span>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]+)<div'
                patron = r'<div class="poster">\s?<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)" alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+>\s*(?P<rating>[0-9.]+)<\/div>(?:<span class="quality">(?:SUB-ITA|)?(?P<quality>|[^<]+)?<\/span>)?[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?<\/a>[^>]+>[^>]+>(?P<year>[^<]+)<\/span>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]+)<div'
        else:
            # TVSHOW
            action = 'episodios'
            if item.args == 'update':
                action = 'findvideos'
                patron = r'<div class="poster"><img src="(?P<thumb>[^"]+)"[^>]+>[^>]+><a href="(?P<url>[^"]+)">[^>]+>(?P<episode>[\d\-x]+)[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)(?:\[(?P<lang>Sub-ITA|Sub-ita)\])?<[^>]+>[^>]+>[^>]+>[^>]+>(?P<quality>[HD]+)?(?:.+?)?/span><p class="serie"'
                pagination = 25
                def itemHook(item):
                    item.contentType = 'episode'
                    return item
            else:
                patron = r'<div class="poster">\s?<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)" alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+> (?P<rating>[0-9.]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA|Sub-ita)\])?<[^>]+>[^>]+>[^>]+>(?P<year>[^<]+)(?:<.*?<div class="texto">(?P<plot>[^<]+))?'

    patronNext = '<span class="current">[^<]+<[^>]+><a href="([^"]+)"'

    #support.regexDbg(item, patron, headers)
    #debug = True
    return locals()


@support.scrape
def episodios(item):
    log()

    patronBlock = r'<h1>.*?[ ]?(?:\[(?P<lang>.+?\]))?</h1>.+?<div class="se-a" '\
                  'style="display:block"><ul class="episodios">(?P<block>.*?)</ul>'\
                  '</div></div></div></div></div>'
    patron = r'<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)">.*?'\
             '<div class="numerando">(?P<episode>[^<]+).*?<div class="episodiotitle">'\
             '[^>]+>(?P<title>[^<]+)<\/a>'
#    debug = True
    return locals()

@support.scrape
def genres(item):
    log(item)

    action='peliculas'
    if item.args == 'genres':
        patronBlock = r'<div class="sidemenu"><h2>Genere</h2>(?P<block>.*?)/li></ul></div>'
    elif item.args == 'year':
        item.args = 'genres'
        patronBlock = r'<div class="sidemenu"><h2>Anno di uscita</h2>(?P<block>.*?)/li></ul></div>'
    elif item.args == 'letter':
        patronBlock = r'<div class="movies-letter">(?P<block>.*?)<div class="clearfix">'

    patronMenu = r'<a(?:.+?)?href="(?P<url>.*?)"[ ]?>(?P<title>.*?)<\/a>'

    return locals()

def search(item, text):
    log(text)
    itemlist = []
    text = text.replace(' ', '+')
    item.url = host + "/?s=" + text
    try:
        item.args = 'search'
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            log("%s" % line)

    return []

def newest(categoria):
    log(categoria)
    itemlist = []
    item = Item()

    if categoria == 'peliculas':
        item.contentType = 'movie'
        item.url = host + '/film/'
    elif categoria == 'series':
        item.args = 'update'
        item.contentType = 'tvshow'
        item.url = host + '/aggiornamenti-serie/'
##    elif categoria == 'anime':
##        item.contentType = 'tvshow'
##        item.url = host + '/anime/'
    try:
        item.action = 'peliculas'
        itemlist = peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            log("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    log()
    matches = support.match(item, patron=[r'class="metaframe rptss" src="([^"]+)"',r' href="#option-\d">([^\s]+)\s*([^\s]+)']).matches
    itemlist = []
    list_url = []
    list_quality = []
    list_servers = []
    for match in matches:
        if type(match) == tuple:
            list_servers.append(match[0])
            list_quality.append(match[1])
        else:
            if 'player.php' in match:
                match = support.httptools.downloadpage(match, follow_redirect=True).url
            list_url.append(match)

    for i, url in enumerate(list_url):
        itemlist.append(support.Item(
            channel=item.channel,
            title=list_servers[i],
            url=url,
            action='play',
            quality=list_quality[i],
            infoLabels = item.infoLabels))

    return support.server(item, itemlist=itemlist)
