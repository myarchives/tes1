# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeleggendari
# ------------------------------------------------------------

from core import support
from lib.js2py.host import jsfunctions

host = support.config.get_channel_url()

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

list_servers = ['verystream','openload','rapidvideo','streamango']
list_quality = ['default']


@support.menu
def mainlist(item):

    anime = [
        ('Leggendari', ['/category/anime-leggendari/', 'peliculas']),
        ('ITA', ['/category/anime-ita/', 'peliculas']),
        ('SUB-ITA', ['/category/anime-sub-ita/', 'peliculas']),
        ('Conclusi', ['/category/serie-anime-concluse/', 'peliculas']),
        ('in Corso', ['/category/serie-anime-in-corso/', 'peliculas']),
        ('Genere', ['', 'genres'])
    ]

    return locals()


def search(item, texto):
    support.log(texto)

    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


@support.scrape
def genres(item):
    blacklist = ['Contattaci','Privacy Policy', 'DMCA']
    patronMenu = r'<a href="(?P<url>[^"]+)">(?P<title>[^<]+)<'
    patronBlock = r'Generi</a>\s*<ul[^>]+>(?P<block>.*?)<\/ul>'
    action = 'peliculas'
    return locals()


@support.scrape
def peliculas(item):
    anime = True
    blacklist = ['top 10 anime da vedere']
    if item.url != host: patronBlock = r'<div id="main-content(?P<block>.*?)<aside'
    patron = r'<figure class="(?:mh-carousel-thumb|mh-posts-grid-thumb)"> <a class="[^"]+" href="(?P<url>[^"]+)" title="(?P<title>.*?)(?: \((?P<year>\d+)\))? (?:(?P<lang>SUB ITA|ITA))(?: (?P<title2>[Mm][Oo][Vv][Ii][Ee]))?[^"]*"><img[^s]+src="(?P<thumb>[^"]+)"[^>]+'
    def itemHook(item):
        if 'movie' in item.title.lower():
            item.title = support.re.sub(' - [Mm][Oo][Vv][Ii][Ee]|[Mm][Oo][Vv][Ii][Ee]','',item.title)
            item.title += support.typo('Movie','_ () bold')
            item.contentType = 'movie'
            item.action = 'findvideos'
        return item
    patronNext = r'<a class="next page-numbers" href="([^"]+)">'
    action = 'episodios'
    return locals()


@support.scrape
def episodios(item):
    data = support.match(item, headers=headers, patronBlock=r'entry-content clearfix">(.*?)class="mh-widget mh-posts-2 widget_text').block
    if not 'pagination clearfix' in data:
        support.log('NOT IN DATA')
        patron = r'<iframe.*?src="(?P<url>[^"]+)"'
        title = item.title
        def fullItemlistHook(itemlist):
            url = ''
            for item in itemlist:
                url += item.url +'\n'
            item = itemlist[0]
            item.data = url
            item.title = title
            item.contentType = 'movie'
            itemlist = []
            itemlist.append(item)
            return itemlist
    else:
        url = item.url
        anime = True
        patronBlock = r'(?:<p style="text-align: left;">|<div class="pagination clearfix">\s*)(?P<block>.*?)</span></a></div>'
        patron = r'(?:<a href="(?P<url>[^"]+)"[^>]+>)?<span class="pagelink">(?P<episode>\d+)'
        def itemHook(item):
            if not item.url:
                item.url = url
            if 'Movie Parte' in data:
                item.title = support.typo(item.fulltitle + ' - Part ','bold') + item.title
                item.contentType = 'movie'
            else:
                item.title = support.typo('Episodio ', 'bold') + item.title
            return item
    return locals()

def check(item):
    data = support.match(item, headers=headers).data
    if 'Lista Episodi' not in data:
        item.data = data
        return findvideos(item)

    data = ''
    return data

def findvideos(item):
    support.log()
    if item.data:
        data = item.data
    else:
        matches = support.match(item, patron=r'<iframe.*?src="(?P<url>[^"]+)"').matches
        data = ''
        if matches:
            for match in matches:
                try: data += str(jsfunctions.unescape(support.re.sub('@|g','%', match)))
                except: data += ''
                data += str(match)
        else:
            data = ''

    return support.server(item,data)
