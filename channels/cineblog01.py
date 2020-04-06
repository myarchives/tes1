# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per cineblog01
# ------------------------------------------------------------

import re

from core import scrapertools, httptools, servertools, tmdb, support
from core.item import Item
from lib import unshortenit
from platformcode import logger, config


def findhost():
    permUrl = httptools.downloadpage('https://cb01-nuovo-indirizzo.info/', follow_redirects=False, only_headers=True).headers
    if 'google' in permUrl['location']:
        host = permUrl['location'].replace('https://www.google.it/search?q=site:', '')
    else:
        host = permUrl['location']
    return host


host = config.get_channel_url(findhost)
headers = [['Referer', host]]

list_servers = ['mixdrop', 'akstream', 'wstream', 'backin']
list_quality = ['HD', 'SD', 'default']

checklinks = config.get_setting('checklinks', 'cineblog01')
checklinks_number = config.get_setting('checklinks_number', 'cineblog01')


@support.menu
def mainlist(item):
    film = [
        ('HD', ['', 'menu', 'Film HD Streaming']),
        ('Generi', ['', 'menu', 'Film per Genere']),
        ('Anni', ['', 'menu', 'Film per Anno']),
        ('Paese', ['', 'menu', 'Film per Paese']),
        ('Ultimi Aggiornati', ['/lista-film-ultimi-100-film-aggiornati/', 'peliculas', 'newest']),
        ('Ultimi Aggiunti', ['/lista-film-ultimi-100-film-aggiunti/', 'peliculas', 'newest'])
    ]
    tvshow = ['/serietv/',
              ('Per Lettera', ['/serietv/', 'menu', 'Serie-Tv per Lettera']),
              ('Per Genere', ['/serietv/', 'menu', 'Serie-Tv per Genere']),
              ('Per anno', ['/serietv/', 'menu', 'Serie-Tv per Anno']),
              ('Ultime Aggiornate', ['/serietv/', 'peliculas', 'newest'])
              ]
    docu = [('Documentari bullet bold', ['/category/documentario/', 'peliculas']),
            ('HD submenu {documentari}', ['category/hd-alta-definizione/documentario-hd/', 'peliculas'])
            ]

    return locals()


@support.scrape
def menu(item):
    patronBlock = item.args + r'<span.*?><\/span>.*?<ul.*?>(?P<block>.*?)<\/ul>'
    patronMenu = r'href="?(?P<url>[^">]+)"?>(?P<title>.*?)<\/a>'
    action = 'peliculas'

    return locals()


# @support.scrape
# def newest(categoria):
#
#     # debug = True
#     patron = r'<a href="?(?P<url>[^">]+)"?>(?P<title>[^<([]+)(?:\[(?P<lang>Sub-ITA|B/N|SUB-ITA)\])?\s*(?:\[(?P<quality>HD|SD|HD/3D)\])?\s*\((?P<year>[0-9]{4})\)<\/a>'

#     if type(categoria) != Item:
#         item = Item()
#     else:
#         item = categoria
#         categoria = 'series' if item.contentType != 'movie' else 'movie'
#     pagination = 20

#     if categoria == 'series':
#         item.contentType = 'tvshow'
#         action = 'episodios'
#         item.url = host + 'serietv/aggiornamento-quotidiano-serie-tv/'
#         patronBlock = r'<article class="sequex-post-content">(?P<block>.*?)</article>'
#         patron = '<a href="(?P<url>[^"]+)".*?>(?P<title>[^<([|]+).*?(?P<lang>ITA|SUB-ITA)?</a'
#     else:
#         item.contentType = 'movie'
#         item.url = host + '/lista-film-ultimi-100-film-aggiunti/'
#         patronBlock = r'Ultimi 100 film aggiunti:(?P<block>.*?)<\/td>'
#     # else:
#     #     patronBlock = r'Ultimi 100 film Aggiornati:(?P<block>.*?)<\/td>'
#     #     item = categoria

#     return locals()


def newest(categoria):
    support.log(categoria)

    item = support.Item()
    try:
        if categoria == "series":
            item.contentType = 'tvshow'
            item.url = host + '/serietv/'  # aggiornamento-quotidiano-serie-tv/'
        else:
            item.contentType = 'movie'
            item.url = host + '/lista-film-ultimi-100-film-aggiunti/'
        item.args = "newest"
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []


def search(item, text):
    support.log(item.url, "search", text)

    try:
        item.url = item.url + "/?s=" + text.replace(' ', '+')
        return peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


@support.scrape
def peliculas(item):
    # esclusione degli articoli 'di servizio'
    blacklist = ['BENVENUTI', 'Richieste Serie TV', 'CB01.UNO &#x25b6; TROVA L&#8217;INDIRIZZO UFFICIALE ',
                 'Aggiornamento Quotidiano Serie TV', 'OSCAR 2019 ▶ CB01.UNO: Vota il tuo film preferito! 🎬',
                 'Openload: la situazione. Benvenuto Verystream', 'Openload: lo volete ancora?',
                 'OSCAR 2020 &#x25b6; VOTA IL TUO FILM PREFERITO! &#x1f3ac;']
    # debug = True
    if 'newest' in item.args:
        if '/serietv/' not in item.url:
            pagination = ''
            patronBlock = r'Ultimi 100 film [^:]+:(?P<block>.*?)<\/td>'
            patron = r'<a href="?(?P<url>[^">]+)"?>(?P<title>[^<([]+)(?:\[(?P<lang>Sub-ITA|B/N|SUB-ITA)\])?\s*(?:\[(?P<quality>HD|SD|HD/3D)\])?\s*\((?P<year>[0-9]{4})\)<\/a>'
            action = 'findvideos'
        else:
            patronBlock = r'Ultime SerieTv aggiornate(?P<block>.*?)Lista'
            patron = r'src="(?P<thumb>[^"]+)" alt="(?P<title>.*?)(?: &#8211; \d+&#215;\d+)?(?:"| &#8211; )(?:(?P<lang>Sub-ITA|ITA))?[^>]*>[^>]+>[^>]+><a href="(?P<url>[^"]+)".*?<div class="rpwe-summary">.*?\((?P<year>\d{4})[^\)]*\) (?P<plot>[^<]+)<'
            action = 'episodios'
    elif '/serietv/' not in item.url:
        patron = r'<div class="card-image">\s<a[^>]+>\s*<img src="(?P<thumb>[^" ]+)" alt[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="?(?P<url>[^" >]+)(?:\/|"|\s+)>(?P<title>[^<[(]+)(?:\[(?P<quality>[A-Za-z0-9/-]+)])? (?:\((?P<year>[0-9]{4})\))?[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<genre>[^<>&Ã¢ÂÂ]+)(?:[^ ]+\s*DURATA\s*(?P<duration>[0-9]+)[^>]+>[^>]+>[^>]+>(?P<plot>[^<>]+))?'
        # patron = r'<div class="?card-image"?>.*?<img src="?(?P<thumb>[^" ]+)"? alt.*?<a href="?(?P<url>[^" >]+)(?:\/|"|\s+)>(?P<title>[^<[(]+)(?:\[(?P<quality>[A-Za-z0-9/-]+)])? (?:\((?P<year>[0-9]{4})\))?.*?<strong>(?P<genre>[^<>&–]+).*?DURATA (?P<duration>[0-9]+).*?<br(?: /)?>(?P<plot>[^<>]+)'
        action = 'findvideos'
    else:
        # debug = True
        patron = r'div class="card-image">.*?<img src="(?P<thumb>[^ ]+)" alt.*?<a href="(?P<url>[^ >]+)">(?P<title>.*?)(?:&#.*?)?(?P<lang>(?:[Ss][Uu][Bb]-)?[Ii][Tt][Aa])?<\/a>.*?(?:<strong><span style="[^"]+">(?P<genre>[^<>0-9(]+)\((?P<year>[0-9]{4}).*?</(?:p|div)>(?P<plot>.*?))?</div'
        action = 'episodios'
        item.contentType = 'tvshow'

    # patronBlock=[r'<div class="?sequex-page-left"?>(?P<block>.*?)<aside class="?sequex-page-right"?>',
    #                                           '<div class="?card-image"?>.*?(?=<div class="?card-image"?>|<div class="?rating"?>)']
    # if 'newest' not in item.args: 
    patronNext = '<a class="?page-link"? href="?([^>]+)"?><i class="fa fa-angle-right">'

    return locals()


@support.scrape
def episodios(item):
    patronBlock = r'(?P<block><div class="sp-head[a-z ]*?" title="Espandi">\s*(?:STAGION[EI]\s*(?:DA\s*[0-9]+\s*A)?\s*[0-9]+|MINISERIE) - (?P<lang>[^-<]+)(?:- (?P<quality>[^-<]+))?.*?[^<>]*?<\/div>.*?)<div class="spdiv">\[riduci\]<\/div>'
    # patron = '(?:<p>|<strong>)(?P<episode>[0-9]+(?:&#215;|×)[0-9]+)\s*(?P<title2>[^&<]*)?(?:&#8211;|-)?\s*(?P<url>.*?)(?:<\/p>|<br)'
    patron = r'(?:/>|<p>|<strong>)(?P<url>.*?(?P<episode>[0-9]+(?:&#215;|ÃÂ)[0-9]+)\s*(?P<title2>.*?)?(?:\s*&#8211;|\s*-|\s*<).*?)(?:<\/p>|<br)'
    def fullItemlistHook(itemlist):
        title_dict = {}
        itlist = []
        special_list = []
        for item in itemlist:
            item.title = re.sub(r'\.(\D)',' \\1', item.title)
            if re.sub(r'(\[[^\]]+\])','',item.title) in [config.get_localized_string(30161),config.get_localized_string(60355),config.get_localized_string(60357)]:
                special_list.append(item)
            else:
                match = support.match(item.title, patron=r'(\d+.\d+)').match.replace('x','')
                item.order = match
                if match not in title_dict:
                    title_dict[match] = item
                elif match in title_dict and item.contentLanguage == title_dict[match].contentLanguage \
                    or item.contentLanguage == 'ITA' and not title_dict[match].contentLanguage \
                    or title_dict[match].contentLanguage == 'ITA' and not item.contentLanguage:
                    title_dict[match].url = item.url
                else:
                    title_dict[match + '1'] = item

        for key, value in title_dict.items():
            itlist.append(value)

        return sorted(itlist, key=lambda it: (it.contentLanguage, int(it.order))) + special_list
    return locals()


def findvideos(item):
    if item.contentType == "episode":
        return findvid_serie(item)

    def load_links(itemlist, re_txt, color, desc_txt, quality=""):
        streaming = scrapertools.find_single_match(data, re_txt).replace('"', '')
        support.log('STREAMING', streaming)
        support.log('STREAMING=', streaming)
        matches = support.match(streaming, patron = r'<td><a.*?href=([^ ]+) [^>]+>([^<]+)<').matches
        for scrapedurl, scrapedtitle in matches:
            logger.debug("##### findvideos %s ## %s ## %s ##" % (desc_txt, scrapedurl, scrapedtitle))
            itemlist.append(
                Item(channel=item.channel,
                     action="play",
                     title=scrapedtitle,
                     url=scrapedurl,
                     server=scrapedtitle,
                     fulltitle=item.fulltitle,
                     thumbnail=item.thumbnail,
                     show=item.show,
                     quality=quality,
                     contentType=item.contentType,
                     folder=False))

    support.log()

    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data
    data = re.sub('\n|\t', '', data)

    # Estrae i contenuti - Streaming
    load_links(itemlist, '<strong>Streamin?g:</strong>(.*?)cbtable', "orange", "Streaming", "SD")

    # Estrae i contenuti - Streaming HD
    load_links(itemlist, '<strong>Streamin?g HD[^<]+</strong>(.*?)cbtable', "yellow", "Streaming HD", "HD")

    # Estrae i contenuti - Streaming 3D
    load_links(itemlist, '<strong>Streamin?g 3D[^<]+</strong>(.*?)cbtable', "pink", "Streaming 3D")

    itemlist = support.server(item, itemlist=itemlist)
    # Extract the quality format
    patronvideos = '>([^<]+)</strong></div>'
    support.addQualityTag(item, itemlist, data, patronvideos)

    return itemlist

    # Estrae i contenuti - Download
    # load_links(itemlist, '<strong>Download:</strong>(.*?)<tableclass=cbtable height=30>', "aqua", "Download")

    # Estrae i contenuti - Download HD
    # load_links(itemlist, '<strong>Download HD[^<]+</strong>(.*?)<tableclass=cbtable width=100% height=20>', "azure", "Download HD")


def findvid_serie(item):
    def load_vid_series(html, item, itemlist, blktxt):
        support.log('HTML',html)
        # Estrae i contenuti
        matches = support.match(html, patron=r'<a href="([^"]+)"[^=]+="_blank"[^>]+>(?!<!--)(.*?)(?:</a>|<img)').matches
        for url, server in matches:
            item = Item(channel=item.channel,
                     action="play",
                     title=server,
                     url=url,
                     server=server,
                     fulltitle=item.fulltitle,
                     show=item.show,
                     quality=blktxt,
                     contentType=item.contentType,
                     folder=False)
            if 'swzz' in item.url: item.url = support.swzz_get_url(item)
            itemlist.append(item)

    support.log()

    itemlist = []
    lnkblk = []
    lnkblkp = []

    data = re.sub(r'((?:<p>|<strong>)?[^\d]*\d*(?:&#215;|Ã)[0-9]+[^<]+)', '' ,item.url)

    # Blocks with split
    blk = re.split(r"(?:>\s*)?([A-Za-z\s0-9]*):\s*<", data, re.S)
    blktxt = ""
    for b in blk:
        if b[0:3] == "a h" or b[0:4] == "<a h":
            load_vid_series("<%s>" % b, item, itemlist, blktxt)
            blktxt = ""
        elif len(b.strip()) > 1:
            blktxt = b.strip()

    return support.server(item, itemlist=itemlist)


def play(item):
    support.log()
    itemlist = []
    ### Handling new cb01 wrapper
    if host[9:] + "/film/" in item.url:
        iurl = httptools.downloadpage(item.url, only_headers=True, follow_redirects=False).headers.get("location", "")
        support.log("/film/ wrapper: ", iurl)
        if iurl:
            item.url = iurl

    if '/goto/' in item.url:
        item.url = item.url.split('/goto/')[-1].decode('base64')

    item.url = item.url.replace('http://cineblog01.uno', 'http://k4pp4.pw')

    logger.debug("##############################################################")
    if "go.php" in item.url:
        data = httptools.downloadpage(item.url).data
        if "window.location.href" in data:
            try:
                data = scrapertools.find_single_match(data, 'window.location.href = "([^"]+)";')
            except IndexError:
                data = httptools.downloadpage(item.url, only_headers=True, follow_redirects=False).headers.get(
                    "location", "")
            data, c = unshortenit.unwrap_30x_only(data)
        else:
            data = scrapertools.find_single_match(data, r'<a href="([^"]+)".*?class="btn-wrapper">.*?licca.*?</a>')

        logger.debug("##### play go.php data ##\n%s\n##" % data)
    else:
        data = support.swzz_get_url(item)

    return servertools.find_video_items(data=data)
