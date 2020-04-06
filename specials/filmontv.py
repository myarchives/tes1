# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale film in tv
# ------------------------------------------------------------

import re
import urllib
from channelselector import get_thumb
from core import httptools, scrapertools, support, tmdb, filetools
from core.item import Item
from platformcode import logger, config, platformtools

host = "https://www.superguidatv.it"

TIMEOUT_TOTAL = 60


def mainlist(item):
    logger.info(" mainlist")
    itemlist = [#Item(channel="search", action='discover_list', title=config.get_localized_string(70309),
               #search_type='list', list_type='movie/now_playing',
               #          thumbnail=get_thumb("now_playing.png")),
               #Item(channel="search", action='discover_list', title=config.get_localized_string(70312),
               #          search_type='list', list_type='tv/on_the_air', thumbnail=get_thumb("on_the_air.png")),
            Item(channel=item.channel,
                     title=config.get_setting("film1", channel="filmontv"),
                     action="now_on_tv",
                     url="%s/film-in-tv/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("film2", channel="filmontv"),
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/premium/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("film3", channel="filmontv"),
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/sky-intrattenimento/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("film4", channel="filmontv"),
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/sky-cinema/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("film5", channel="filmontv"),
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/sky-primafila/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("now1", channel="filmontv"),
                     action="now_on_misc",
                     url="%s/ora-in-onda/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("now2", channel="filmontv"),
                     action="now_on_misc",
                     url="%s/ora-in-onda/premium/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("now3", channel="filmontv"),
                     action="now_on_misc",
                     url="%s/ora-in-onda/sky-intrattenimento/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("now4", channel="filmontv"),
                     action="now_on_misc",
                     url="%s/ora-in-onda/sky-doc-e-lifestyle/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title=config.get_setting("now5", channel="filmontv"),
                     action="now_on_misc_film",
                     url="%s/ora-in-onda/sky-cinema/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel, 
                    title="Personalizza Oggi in TV",
                    action="server_config", 
                    config="filmontv", 
                    folder=False, 
                    thumbnail=item.thumbnail)]

    return itemlist

def server_config(item):
    return platformtools.show_channel_settings(channelpath=filetools.join(config.get_runtime_path(), "server", item.config))

def now_on_misc_film(item):
    logger.info("filmontv tvoggi")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    #patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    patron = r'table-cell[;" ]*alt="([^"]+)".*?backdrop" alt="([^"]+)"[ ]*src="([^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedchannel, scrapedtitle, scrapedthumbnail in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        #infoLabels["year"] = ""
        infoLabels['title'] = "movie"
        itemlist.append(
            Item(channel=item.channel,
                 action="new_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                 title="[B]" + scrapedtitle + "[/B] - " + scrapedchannel,
                 fulltitle=scrapedtitle,
                 mode='all',
                 search_text=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail.replace("?width=320", "?width=640"),
                 contentTitle=scrapedtitle,
                 contentType='movie',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def now_on_misc(item):
    logger.info("filmontv tvoggi")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    #patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    patron = r'table-cell[;" ]*alt="([^"]+)".*?backdrop" alt="([^"]+)"[ ]*src="([^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedchannel, scrapedtitle, scrapedthumbnail in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        infoLabels["year"] = ""
        infoLabels['tvshowtitle'] = scrapedtitle
        itemlist.append(
            Item(channel=item.channel,
                 action="new_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'tvshow',
                 title="[B]" + scrapedtitle + "[/B] - " + scrapedchannel,
                 fulltitle=scrapedtitle,
                 mode='all',
                 search_text=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail.replace("?width=320", "?width=640"),
                 contentTitle=scrapedtitle,
                 contentType='tvshow',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def now_on_tv(item):
    logger.info("filmontv tvoggi")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    #patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    patron = r'view_logo" alt="([a-zA-Z 0-9]*)".*?spanMovieDuration">([^<]+).*?spanTitleMovie">([A-Za-z ,0-9\.À-ÖØ-öø-ÿ\-\']*).*?GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*).*?src="([a-zA-Z:\/\.0-9?]*).*?Year">([A-Z 0-9a-z]*)'    
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedchannel, scrapedduration, scrapedtitle, scrapedgender, scrapedthumbnail, scrapedyear in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        infoLabels["year"] = scrapedyear
        itemlist.append(
            Item(channel=item.channel,
                 action="new_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                 title="[B]" + scrapedtitle + "[/B] - " + scrapedchannel + " - " + scrapedduration,
                 fulltitle="[B]" + scrapedtitle + "[/B] - " + scrapedchannel+ " - " + scrapedduration,
                 url=scrapedurl,
                 mode='all',
                 search_text=scrapedtitle,
                 thumbnail=scrapedthumbnail.replace("?width=240", "?width=480"),
                 contentTitle=scrapedtitle,
                 contentType='movie',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def primafila(item):
    logger.info("filmontv tvoggi")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    #patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ]*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?=]*)'
    patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedtitle, scrapedgender, scrapedthumbnail, scrapedyear in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        infoLabels["year"] = scrapedyear
        itemlist.append(
            Item(channel=item.channel,
                 action="new_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 mode='all',
                 search_text=scrapedtitle,
                 thumbnail=scrapedthumbnail.replace("?width=240", "?width=480"),
                 contentTitle=scrapedtitle,
                 contentType='movie',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def new_search(item):
    from specials import search
    return search.new_search(item)
