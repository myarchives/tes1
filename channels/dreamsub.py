# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'dreamsub'
# ------------------------------------------------------------

from core import support

host = support.config.get_channel_url()
headers = [['Referer', host]]

@support.menu
def mainlist(item):
    support.log(item)

    anime = ['/search?typeY=tv',
            ('Movie', ['/search?typeY=movie', 'peliculas', '', 'movie']),
            ('OAV', ['/search?typeY=oav', 'peliculas', '', 'tvshow']),
            ('Spinoff', ['/search?typeY=spinoff', 'peliculas', '', 'tvshow']),
            ('Generi', ['','menu','Generi']),
            ('Stato', ['','menu','Stato']),
            ('Ultimi Episodi', ['', 'peliculas', ['last', 'episodiRecenti']]),
            ('Ultimi Aggiornamenti', ['', 'peliculas', ['last', 'episodiNuovi']])
             ]

    return locals()


@support.scrape
def menu(item):
    item.contentType = ''
    action = 'peliculas'

    patronBlock = r'<div class="filter-header"><b>%s</b>(?P<block>.*?)<div class="filter-box">' % item.args
    patronMenu = r'<a class="[^"]+" data-state="[^"]+" (?P<other>[^>]+)>[^>]+></i>[^>]+></i>[^>]+></i>(?P<title>[^>]+)</a>'

    def itemHook(item):
        support.log(item.type)
        for Type, ID in support.match(item.other, patron=r'data-type="([^"]+)" data-id="([^"]+)"').matches:
            item.url = host + '/search?' + Type + 'Y=' + ID
        return item
    return locals()


def search(item, text):
    support.log(text)

    text = text.replace(' ', '+')
    item.url = host + '/search/' + text
    item.args = 'search'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log('search log:', line)
        return []


def newest(categoria):
    support.log(categoria)
    item = support.Item()
    try:
        if categoria == "anime":
            item.url = host
            item.args = ['last', 'episodiNuovi']
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []



@support.scrape
def peliculas(item):
    anime = True
    if 'movie' in item.url:
        item.contentType = 'movie'
        action = 'findvideos'
    else:
        item.contentType = 'tvshow'
        action = 'episodios'

    if len(item.args) > 1 and item.args[0] == 'last':
        patronBlock = r'<div id="%s"[^>]+>(?P<block>.*?)<div class="vistaDettagliata"' % item.args[1]
        patron = r'<li>\s*<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)" class="thumb">[^>]+>[^>]+>[^>]+>\s*[EePp]+\s*(?P<episode>\d+)[^>]+>[^>]+>[^>]+>(?P<lang>[^<]*)<[^>]+>[^>]+>\s<img src="(?P<thumb>[^"]+)"'
    else:
        patron = r'<div class="showStreaming"> <b>(?P<title>[^<]+)[^>]+>[^>]+>\s*Stato streaming: (?:[^<]+)<[^>]+>[^>]+>\s*Lingua:[ ](?P<lang>ITA\/JAP|ITA|JAP|SUB ITA)?[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<div class="[^"]+" style="background: url\((?P<thumb>[^\)]+)\)'
        patronNext = '<li class="currentPage">[^>]+><li[^<]+<a href="([^"]+)">'

    return locals()


@support.scrape
def episodios(item):
    anime = True
    pagination = 100

    if item.data:
        data = item.data

    patron = r'<div class="sli-name">\s*<a href="(?P<url>[^"]+)"[^>]+>(?P<title>[^<]+)<'

    return locals()


def findvideos(item):
    itemlist = []
    support.log()
    # support.dbg()

    matches = support.match(item, patron=r'href="([^"]+)"', patronBlock=r'<div style="white-space: (.*?)<div id="main-content"')

    if not matches.matches and item.contentType != 'episode':
        item.data = matches.data
        item.contentType = 'tvshow'
        return episodios(item)

    if 'vvvvid' in matches.data:
        itemlist.append(
                support.Item(channel=item.channel,
                            action="play",
                            contentType=item.contentType,
                            title='vvvid',
                            url=support.match(matches.data, patron=r'(http://www.vvvvid[^"]+)').match,
                            server='vvvvid',
                            ))
    else:
    # matches.matches.sort()
        support.log('VIDEO')
        for url in matches.matches:
            lang = url.split('/')[-2]
            if 'ita' in lang.lower():
                language = 'ITA'
            if 'sub' in lang.lower():
                language = 'Sub-' + language
            quality = url.split('/')[-1]

            itemlist.append(
                support.Item(channel=item.channel,
                            action="play",
                            contentType=item.contentType,
                            title=language,
                            url=url,
                            contentLanguage = language,
                            quality = quality,
                            order = quality.replace('p','').zfill(4),
                            server='directo',
                            ))

    itemlist.sort(key=lambda x: (x.title, x.order), reverse=False)
    return support.server(item, itemlist=itemlist)