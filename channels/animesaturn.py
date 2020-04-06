# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeSaturn
# ----------------------------------------------------------

from core import support

host = support.config.get_channel_url()
headers={'X-Requested-With': 'XMLHttpRequest'}


list_servers = ['directo', 'fembed', 'animeworld']
list_quality = ['default', '480p', '720p', '1080p']

@support.menu
def mainlist(item):

    anime = ['/animelist?load_all=1',
             ('Più Votati',['/toplist','menu', 'top']),
             ('In Corso',['/animeincorso','peliculas','incorso']),
             ('Ultimi Episodi',['/fetch_pages.php?request=episodes','peliculas','updated'])]

    return locals()


@support.scrape
def search(item, texto):
    search = texto
    item.contentType = 'tvshow'
    anime = True
    patron = r'<a href="(?P<url>[^"]+)"[^>]+> <span>(?P<title>[^<\(]+)(?:\s*\((?P<year>\d+)\))?(?:\s*\((?P<lang>[A-Za-z-]+)\))?'
    action = 'check'
    return locals()


def newest(categoria):
    support.log()
    itemlist = []
    item = support.Item()
    try:
        if categoria == "anime":
            item.url = host + '/fetch_pages.php?request=episodes'
            item.args = "updated"
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []

    return itemlist

@support.scrape
def menu(item):
    patronMenu = r'<div class="col-md-13 bg-dark-as-box-shadow p-2 text-white text-center">(?P<title>[^"<]+)<(?P<url>.*?)(?:"lista-top"|"clearfix")'
    action = 'peliculas'
    item.args = 'top'
    return locals()


@support.scrape
def peliculas(item):
    anime = True

    deflang= 'Sub-ITA'
    action = 'check'

    page = None
    post = "page=" + str(item.page if item.page else 1) if item.page > 1 else None

    if item.args == 'top':
        data=item.url
        patron = r'light">(?P<title2>[^<]+)</div>\s(?P<title>[^<]+)[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)">(?:<a[^>]+>|\s*)<img alt="[^"]+" src="(?P<thumb>[^"]+)"'

    else:
        data = support.match(item, post=post, headers=headers).data
        if item.args == 'updated':
            page= support.match(data, patron=r'data-page="(\d+)" title="Next">').match
            patron = r'<a href="(?P<url>[^"]+)" title="(?P<title>[^"(]+)(?:\s*\((?P<year>\d+)\))?(?:\s*\((?P<lang>[A-Za-z-]+)\))?"><img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s\s*(?P<type>[^\s]+)\s*(?P<episode>\d+)'
            typeContentDict = {'Movie':'movie', 'Episodio':'episode'} #item.contentType='episode'
            action = 'findvideos'
            def itemlistHook(itemlist):
                if page:
                    itemlist.append(
                        support.Item(channel=item.channel,
                            action = item.action,
                            contentType=item.contentType,
                            title=support.typo(support.config.get_localized_string(30992), 'color kod bold'),
                            url=item.url,
                            page= page,
                            args=item.args,
                            thumbnail=support.thumb()))
                    return itemlist
        else:
            pagination = ''
            if item.args == 'incorso':
                patron = r'<a href="(?P<url>[^"]+)"[^>]+>(?P<title>[^<(]+)(?:\s*\((?P<year>\d+)\))?(?:\s*\((?P<lang>[A-za-z-]+)\))?</a>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<img width="[^"]+" height="[^"]+" src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]+)<'
            else:
                patron = r'href="(?P<url>[^"]+)"[^>]+>[^>]+>(?P<title>.+?)(?:\((?P<lang>ITA)\))?(?:(?P<year>\((\d+)\)))?</span>'

    return locals()


def check(item):
    movie = support.match(item, patron=r'Episodi:</b> (\d*) Movie')
    anime_id = support.match(movie.data, patron=r'anime_id=(\d+)').match
    item.url = host + "/loading_anime?anime_id=" + anime_id
    if movie.match:
        item.contentType = 'movie'
        episodes = episodios(item)
        if len(episodes) > 0: item.url = episodes[0].url
        return findvideos(item)
    else:
        item.contentType = 'tvshow'
        return episodios(item)


@support.scrape
def episodios(item):
    if item.contentType != 'movie': anime = True
    patron = r'<a href="(?P<url>[^"]+)"[^>]+>\s*(?P<title>[^<]+)</a>'
    return locals()


def findvideos(item):
    support.log()
    itemlist = []
    url = support.match(item, patron=r'<a href="([^"]+)">[^>]+>[^>]+>G', headers=headers, debug=False).match
    support.log(url)
    if url:
        links = support.match(url, patron=r'(?:<source type="[^"]+"\s*src=|file:\s*)"([^"]+)"', headers=headers, debug=False).matches
        for link in links:
            itemlist.append(
                support.Item(channel=item.channel,
                            action="play",
                            title='Diretto',
                            quality='',
                            url=link,
                            server='directo',
                            fulltitle=item.fulltitle,
                            show=item.show,
                            contentType=item.contentType,
                            folder=False))
    return support.server(item, itemlist=itemlist)









