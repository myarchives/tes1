# -*- coding: utf-8 -*-

import glob
import os
import sys

from core import channeltools
from core.item import Item
from platformcode.unify import thumb_dict
from platformcode import config, logger, unify
import xbmcaddon
addon = xbmcaddon.Addon('plugin.video.kod')
downloadenabled = addon.getSetting('downloadenabled')

def getmainlist(view="thumb_"):
    logger.info()
    itemlist = list()

    if config.dev_mode():
        itemlist.append(Item(title="Redirect", channel="checkhost", action="check_channels",
                            thumbnail='',
                            category=config.get_localized_string(30119), viewmode="thumbnails"))
    # Añade los canales que forman el menú principal
    if addon.getSetting('enable_news_menu') == "true":
        # itemlist.append(Item(title=config.get_localized_string(30130), channel="news", action="mainlist",
        #                     thumbnail=get_thumb("news.png", view),
        #                     category=config.get_localized_string(30119), viewmode="thumbnails",
        #                     context=CONTEXT + [{"title": config.get_localized_string(70285), "channel": "news", "action": "menu_opciones","goto": True}]))
        itemlist.append(Item(title=config.get_localized_string(30130), channel="news", action="mainlist",
                            thumbnail=get_thumb("news.png", view),
                            category=config.get_localized_string(30119), viewmode="thumbnails",
                            context=[{"title": config.get_localized_string(70285), "channel": "shortcuts", "action": "SettingOnPosition", "category":5}]))

    if addon.getSetting('enable_channels_menu') == "true":
        itemlist.append(Item(title=config.get_localized_string(30118), channel="channelselector", action="getchanneltypes",
                            thumbnail=get_thumb("channels.png", view), view=view,
                            category=config.get_localized_string(30119), viewmode="thumbnails"))

    if addon.getSetting('enable_search_menu') == "true":
        # itemlist.append(Item(title=config.get_localized_string(30103), channel="search", path='special', action="mainlist",
        #                     thumbnail=get_thumb("search.png", view),
        #                     category=config.get_localized_string(30119), viewmode="list",
        #                     context = CONTEXT + [{"title": config.get_localized_string(60412), "action": "setting_channel_new", "channel": "search"},
        #                                          {"title": config.get_localized_string(70286), "action": "settings", "channel": "search"}]))
        itemlist.append(Item(title=config.get_localized_string(30103), channel="search", path='special', action="mainlist",
                            thumbnail=get_thumb("search.png", view),
                            category=config.get_localized_string(30119), viewmode="list",
                            context = [{"title": config.get_localized_string(60412), "action": "setting_channel_new", "channel": "search"},
                                                 {"title": config.get_localized_string(70286), "channel": "shortcuts", "action": "SettingOnPosition", "category":3}]))

    if addon.getSetting('enable_onair_menu') == "true":
        itemlist.append(Item(channel="filmontv", action="mainlist", title=config.get_localized_string(50001),
                            thumbnail=get_thumb("on_the_air.png"), viewmode="thumbnails"))

    if addon.getSetting('enable_link_menu') == "true":
        itemlist.append(Item(title=config.get_localized_string(70527), channel="kodfavorites", action="mainlist",
                            thumbnail=get_thumb("mylink.png", view), view=view,
                            category=config.get_localized_string(70527), viewmode="thumbnails"))

    if addon.getSetting('enable_fav_menu') == "true":
        itemlist.append(Item(title=config.get_localized_string(30102), channel="favorites", action="mainlist",
                            thumbnail=get_thumb("favorites.png", view),
                            category=config.get_localized_string(30102), viewmode="thumbnails"))

    if config.get_videolibrary_support() and addon.getSetting('enable_library_menu') == "true":
        # itemlist.append(Item(title=config.get_localized_string(30131), channel="videolibrary", action="mainlist",
        #                      thumbnail=get_thumb("videolibrary.png", view),
        #                      category=config.get_localized_string(30119), viewmode="thumbnails",
        #                      context=CONTEXT + [{"title": config.get_localized_string(70287), "channel": "videolibrary",
        #                                "action": "channel_config"}]))
        itemlist.append(Item(title=config.get_localized_string(30131), channel="videolibrary", action="mainlist",
                             thumbnail=get_thumb("videolibrary.png", view),
                             category=config.get_localized_string(30119), viewmode="thumbnails",
                             context=[{"title": config.get_localized_string(70287), "channel": "shortcuts", "action": "SettingOnPosition", "category":2},
                                                {"title": config.get_localized_string(60568), "channel": "videolibrary", "action": "update_videolibrary"}]))
    if downloadenabled != "false":
        # itemlist.append(Item(title=config.get_localized_string(30101), channel="downloads", action="mainlist",
        #                     thumbnail=get_thumb("downloads.png", view), viewmode="list",
        #                     context=CONTEXT + [{"title": config.get_localized_string(70288), "channel": "setting", "config": "downloads",
        #                             "action": "channel_config"}]))
        itemlist.append(Item(title=config.get_localized_string(30101), channel="downloads", action="mainlist",
                            thumbnail=get_thumb("downloads.png", view), viewmode="list",
                            context=[{"title": config.get_localized_string(70288), "channel": "shortcuts", "action": "SettingOnPosition", "category":4}]))

    thumb_setting = "setting_%s.png" % 0  # config.get_setting("plugin_updates_available")

    # itemlist.append(Item(title=config.get_localized_string(30100), channel="setting", action="mainlist",
    #                      thumbnail=get_thumb(thumb_setting, view),
    #                      category=config.get_localized_string(30100), viewmode="list"))
    itemlist.append(Item(title=config.get_localized_string(30100), channel="setting", action="settings",
                         thumbnail=get_thumb(thumb_setting, view),
                         category=config.get_localized_string(30100), viewmode="list"))
    itemlist.append(Item(title=config.get_localized_string(30104) + " (v" + config.get_addon_version(with_fix=True) + ")", channel="help", action="mainlist",
                         thumbnail=get_thumb("help.png", view),
                         category=config.get_localized_string(30104), viewmode="list"))
    return itemlist


def getchanneltypes(view="thumb_"):
    logger.info()

    # Lista de categorias
    channel_types = ["movie", "tvshow", "anime", "documentary", "vos", "direct", "live", "music"] # , "torrent"

    if config.get_setting("adult_mode") != 0:
        channel_types.append("adult")

    # channel_language = config.get_setting("channel_language", default="all")
    channel_language = auto_filter()
    logger.info("channel_language=%s" % channel_language)

    # Ahora construye el itemlist ordenadamente
    itemlist = list()
    title = config.get_localized_string(30121)
    itemlist.append(Item(title=title, channel="channelselector", action="filterchannels", view=view,
                         category=title, channel_type="all", thumbnail=get_thumb("all.png", view),
                         viewmode="thumbnails"))

    for channel_type in channel_types:
        title = config.get_localized_category(channel_type)
        itemlist.append(Item(title=title, channel="channelselector", action="filterchannels", category=title,
                             channel_type=channel_type, viewmode="thumbnails",
                             thumbnail=get_thumb("%s.png" % channel_type, view)))

    # itemlist.append(Item(title='Oggi in TV', channel="filmontv", action="mainlist", view=view,
    #                      category=title, channel_type="all", thumbnail=get_thumb("on_the_air.png", view),
    #                      viewmode="thumbnails"))



    itemlist.append(Item(title=config.get_localized_string(70685), channel="community", action="mainlist", view=view,
                         category=config.get_localized_string(70685), channel_type="all", thumbnail=get_thumb("community.png", view),
                         viewmode="thumbnails"))
    return itemlist


def filterchannels(category, view="thumb_"):
    logger.info('Filterchannl'+category)

    channelslist = []

    # Si category = "allchannelstatus" es que estamos activando/desactivando canales
    appenddisabledchannels = False
    if category == "allchannelstatus":
        category = "all"
        appenddisabledchannels = True

    # Lee la lista de canales
    if category != 'adult':
        channel_path = os.path.join(config.get_runtime_path(), 'channels', '*.json')
    else:
        channel_path = os.path.join(config.get_runtime_path(), 'channels', 'porn', '*.json')
    logger.info("channel_path = %s" % channel_path)

    channel_files = glob.glob(channel_path)
    logger.info("channel_files encontrados %s" % (len(channel_files)))

    # channel_language = config.get_setting("channel_language", default="all")
    channel_language = auto_filter()
    logger.info("channel_language=%s" % channel_language)

    for channel_path in channel_files:
        logger.info("channel in for = %s" % channel_path)

        channel = os.path.basename(channel_path).replace(".json", "")

        try:
            channel_parameters = channeltools.get_channel_parameters(channel)

            if channel_parameters["channel"] == 'community':
                continue

            # # si el canal no es compatible, no se muestra
            # if not channel_parameters["compatible"]:
            #     continue

            # Si no es un canal lo saltamos
            if not channel_parameters["channel"]:
                continue
            logger.info("channel_parameters=%s" % repr(channel_parameters))

            # Si prefiere el banner y el canal lo tiene, cambia ahora de idea
            if view == "banner_" and "banner" in channel_parameters:
                channel_parameters["thumbnail"] = channel_parameters["banner"]

            # si el canal está desactivado no se muestra el canal en la lista
            if not channel_parameters["active"]:
                continue

            # Se salta el canal si no está activo y no estamos activando/desactivando los canales
            channel_status = config.get_setting("enabled", channel_parameters["channel"])

            if channel_status is None:
                # si channel_status no existe es que NO HAY valor en _data.json.
                # como hemos llegado hasta aquí (el canal está activo en channel.json), se devuelve True
                channel_status = True

            if not channel_status:
                # si obtenemos el listado de canales desde "activar/desactivar canales", y el canal está desactivado
                # lo mostramos, si estamos listando todos los canales desde el listado general y está desactivado,
                # no se muestra
                if not appenddisabledchannels:
                    continue

            # Se salta el canal para adultos si el modo adultos está desactivado
            if channel_parameters["adult"] and config.get_setting("adult_mode") == 0:
                continue

            # Se salta el canal si está en un idioma filtrado
            # Se muestran todos los canales si se elige "all" en el filtrado de idioma
            # Se muestran sólo los idiomas filtrados, cast o lat
            # Los canales de adultos se mostrarán siempre que estén activos

            # for channel_language_list in channel_language_list:
            #     if c in channel_parameters["language"]:
            #         L = True
            #     else:
            #         L = False
            # logger.info('CCLANG= ' + channel_language + ' ' + str(channel_language_list))
            if channel_language != "all" and "*" not in channel_parameters["language"] \
                 and channel_language not in str(channel_parameters["language"]):
                continue

            # Se salta el canal si está en una categoria filtrado
            if category != "all" and category not in channel_parameters["categories"]:
                continue

            # Si tiene configuración añadimos un item en el contexto
            context = []
            if channel_parameters["has_settings"]:
                context.append({"title": config.get_localized_string(70525), "channel": "setting", "action": "channel_config",
                                "config": channel_parameters["channel"]})

            channel_info = set_channel_info(channel_parameters)
            # Si ha llegado hasta aquí, lo añade
            channelslist.append(Item(title=channel_parameters["title"], channel=channel_parameters["channel"],
                                     action="mainlist", thumbnail=channel_parameters["thumbnail"],
                                     fanart=channel_parameters["fanart"], plot=channel_info, category=channel_parameters["title"],
                                     language=channel_parameters["language"], viewmode="list", context=context))

        except:
            logger.error("Se ha producido un error al leer los datos del canal '%s'" % channel)
            import traceback
            logger.error(traceback.format_exc())

    channelslist.sort(key=lambda item: item.title.lower().strip())

    if category == "all":
        channel_parameters = channeltools.get_channel_parameters('url')
        # Si prefiere el banner y el canal lo tiene, cambia ahora de idea
        if view == "banner_" and "banner" in channel_parameters:
            channel_parameters["thumbnail"] = channel_parameters["banner"]

        channelslist.insert(0, Item(title=config.get_localized_string(60088), action="mainlist", channel="url",
                                    thumbnail=channel_parameters["thumbnail"], type="generic", viewmode="list"))

    if category in ['movie', 'tvshow']:
        titles = [config.get_localized_string(70028), config.get_localized_string(30985), config.get_localized_string(70559), config.get_localized_string(60264), config.get_localized_string(70560)]
        ids = ['popular', 'top_rated', 'now_playing', 'on_the_air']
        for x in range(0,3):
            if x == 2 and category != 'movie':
                title=titles[x+1]
                id = ids[x+1]
            else:
                title=titles[x]
                id = ids[x]
            channelslist.insert(x,
                Item(channel='search', action='discover_list', title=title, search_type='list',
                     list_type='%s/%s' % (category.replace('show',''), id), mode=category, thumbnail=get_thumb(id+".png")))

        channelslist.insert(3, Item(channel='search', action='genres_menu', title=config.get_localized_string(30987),
                                    type=category.replace('show',''), mode=category ,thumbnail=get_thumb("genres.png")))

    return channelslist


def get_thumb(thumb_name, view="thumb_", auto=False):

    if auto:
        thumbnail = ''

        thumb_name = unify.set_genre(unify.simplify(thumb_name))

        if thumb_name in thumb_dict:
            thumbnail = thumb_dict[thumb_name]
        return thumbnail

    else:
        icon_pack_name = config.get_setting('icon_set', default="default")
        media_path = os.path.join("https://raw.githubusercontent.com/kodiondemand/media/master/themes", icon_pack_name)

        if config.get_setting('enable_custom_theme') and config.get_setting('custom_theme') and os.path.isfile(config.get_setting('custom_theme') + view + thumb_name):
            media_path = config.get_setting('custom_theme')

        if thumb_name.startswith('http'):
            thumbnail = thumb_name
        else:
            thumbnail = os.path.join(media_path, view + thumb_name)
        if 'http' in thumbnail:
            thumbnail = thumbnail.replace('\\','/')
        return thumbnail


def set_channel_info(parameters):
    logger.info()

    info = ''
    language = ''
    content = ''
    langs = parameters['language']
    lang_dict = {'ita':'Italiano',
                 'sub-ita':'Sottotitolato in Italiano',
                 '*':'Italiano, Sottotitolato in Italiano'}

    for lang in langs:
        # if 'vos' in parameters['categories']:
        #     lang = '*'
        # if 'sub-ita' in parameters['categories']:
        #     lang = 'ita'

        if lang in lang_dict:
            if language != '' and language != '*' and not parameters['adult']:
                language = '%s, %s' % (language, lang_dict[lang])
            elif not parameters['adult']:
                language = lang_dict[lang]
        if lang == '*':
            break

    categories = parameters['categories']
    for cat in categories:
        if content != '':
            content = '%s, %s' % (content, config.get_localized_category(cat))
        else:
            content = config.get_localized_category(cat)

    info = '[B]' + config.get_localized_string(70567) + ' [/B]' + content + '\n\n'
    info += '[B]' + config.get_localized_string(70568) + ' [/B] ' + language
    return info


def auto_filter(auto_lang=False):
    list_lang = ['ita', 'vos', 'sub-ita']
    if config.get_setting("channel_language") == 'auto' or auto_lang == True:
        lang = config.get_localized_string(20001)

    else:
        lang = config.get_setting("channel_language", default="all")

    if lang not in list_lang:
        lang = 'all'

    return lang

    # import xbmc, xbmcaddon

    # addon = xbmcaddon.Addon('metadata.themoviedb.org')
    # def_lang = addon.getSetting('language')
    # lang = 'all'
    # lang_list = ['all']

    # lang_dict = {'it':'ita'}
    # lang_list_dict = {'it':['ita','vosi']}

    # if config.get_setting("channel_language") == 'auto' or auto_lang == True:
    #     lang = lang_dict[def_lang]
    #     lang_list = lang_list_dict[def_lang]

    # else:
    #     lang = config.get_setting("channel_language", default="all")
    #     lang_list = lang_list_dict[def_lang]

    # return lang, lang_list


def thumb(item_or_itemlist=None, genre=False, thumb=''):
    import re
    icon_dict = {'movie':['film', 'movie'],
                 'tvshow':['serie','tv','episodi','episodio','fiction', 'show'],
                 'documentary':['documentari','documentario', 'documentary'],
                 'teenager':['ragazzi','teenager', 'teen'],
                 'learning':['learning'],
                 'all':['tutti', 'all'],
                 'news':['novità', "novita'", 'aggiornamenti', 'nuovi', 'nuove', 'new', 'newest', 'news'],
                 'now_playing':['cinema', 'in sala'],
                 'anime':['anime'],
                 'genres':['genere', 'generi', 'categorie', 'categoria', 'category'],
                 'animation': ['animazione', 'cartoni', 'cartoon', 'animation'],
                 'action':['azione', 'arti marziali', 'action'],
                 'adventure': ['avventura', 'adventure'],
                 'biographical':['biografico', 'biographical'],
                 'comedy':['comico', 'commedia', 'demenziale', 'comedy'],
                 'adult':['erotico', 'hentai', 'harem', 'ecchi', 'adult'],
                 'drama':['drammatico', 'drama'],
                 'syfy':['fantascienza', 'science fiction', 'syfy'],
                 'fantasy':['fantasy', 'magia', 'magic'],
                 'crime':['gangster','poliziesco', 'crime', 'crimine'],
                 'grotesque':['grottesco', 'grotesque'],
                 'war':['guerra', 'war'],
                 'children':['bambini', 'kids'],
                 'horror':['horror'],
                 'music':['musical', 'musica', 'music'],
                 'mistery':['mistero', 'giallo', 'mystery'],
                 'noir':['noir'],
                 'popular' : ['popolari','popolare', 'più visti'],
                 'thriller':['thriller'],
                 'top_rated' : ['fortunato', 'votati', 'lucky'],
                 'on_the_air' : ['corso', 'onda', 'diretta', 'dirette'],
                 'western':['western'],
                 'vos':['sub','sub-ita'],
                 'romance':['romantico','sentimentale', 'romance'],
                 'family':['famiglia','famiglie', 'family', 'historical'],
                 'historical':['storico', 'history', 'storia'],
                 'az':['lettera','lista','alfabetico','a-z', 'alphabetical'],
                 'year':['anno', 'anni', 'year'],
                 'update':['replay', 'update'],
                 'autoplay':[config.get_localized_string(60071)]
                }

    suffix_dict = {'_hd':['hd','altadefinizione','alta definizione'],
                '_4k':['4K'],
                '_az':['lettera','lista','alfabetico','a-z', 'alphabetical'],
                '_year':['anno', 'anni', 'year'],
                '_genre':['genere', 'generi', 'categorie', 'categoria']}

    search = ['cerca', 'search']

    search_suffix ={'_movie':['film', 'movie'],
                    '_tvshow':['serie','tv', 'fiction']}

    def autoselect_thumb(item, genre):
        if genre == False:
            for thumb, titles in icon_dict.items():
                if any( word in re.split(r'\.|\{|\}|\[|\]|\(|\)| ',item.title.lower()) for word in search):
                    thumb = 'search'
                    for suffix, titles in search_suffix.items():
                        if any( word in re.split(r'\.|\{|\}|\[|\]|\(|\)| ',item.title.lower()) for word in titles ):
                            thumb = thumb + suffix
                    item.thumbnail = get_thumb(thumb + '.png')
                elif any( word in re.split(r'\.|\{|\}|\[|\]|\(|\)| ',item.title.lower()) for word in titles ):
                    if thumb == 'movie' or thumb == 'tvshow':
                        for suffix, titles in suffix_dict.items():
                            if any( word in re.split(r'\.|\{|\}|\[|\]|\(|\)| ',item.title.lower()) for word in titles ):
                                thumb = thumb + suffix
                        item.thumbnail = get_thumb(thumb + '.png')
                    else: item.thumbnail = get_thumb(thumb + '.png')
                else:
                    thumb = item.thumbnail

        else:
            for thumb, titles in icon_dict.items():
                if any(word in re.split(r'\.|\{|\}|\[|\]|\(|\)| ',item.title.lower()) for word in titles ):
                    item.thumbnail = get_thumb(thumb + '.png')
                else:
                    thumb = item.thumbnail

        item.title = re.sub(r'\s*\{[^\}]+\}','',item.title)
        return item
    if item_or_itemlist:
        if type(item_or_itemlist) == list:
            for item in item_or_itemlist:
                autoselect_thumb(item, genre)
            return item_or_itemlist

        else:
            return autoselect_thumb(item_or_itemlist, genre)

    elif thumb:
        return get_thumb(thumb)
    else:
        return get_thumb('next.png')
