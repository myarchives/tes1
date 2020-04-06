# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC Library Tools
# ------------------------------------------------------------
from future import standard_library
standard_library.install_aliases()
#from builtins import str
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
    
import os
import threading
import time
import re

import xbmc
from core import filetools
from core import jsontools
from platformcode import config, logger
from platformcode import platformtools
from core import scrapertools
from xml.dom import minidom


def mark_auto_as_watched(item):
    def mark_as_watched_subThread(item):
        logger.info()
        # logger.debug("item:\n" + item.tostring('\n'))

        condicion = config.get_setting("watched_setting", "videolibrary")

        time_limit = time.time() + 30
        while not platformtools.is_playing() and time.time() < time_limit:
            time.sleep(1)

        sync_with_trakt = False

        while platformtools.is_playing():
            tiempo_actual = xbmc.Player().getTime()
            totaltime = xbmc.Player().getTotalTime()

            mark_time = 0
            if condicion == 0:  # '5 minutos'
                mark_time = 300
            elif condicion == 1:  # '30%'
                mark_time = totaltime * 0.3
            elif condicion == 2:  # '50%'
                mark_time = totaltime * 0.5
            elif condicion == 3:  # '80%'
                mark_time = totaltime * 0.8
            elif condicion == 4:  # '0 seg'
                mark_time = -1

            # logger.debug(str(tiempo_actual))
            # logger.debug(str(mark_time))

            if tiempo_actual > mark_time:
                logger.debug("marcado")
                item.playcount = 1
                sync_with_trakt = True
                from specials import videolibrary
                videolibrary.mark_content_as_watched2(item)
                break

            time.sleep(30)

        # Sincronizacion silenciosa con Trakt
        if sync_with_trakt:
            if config.get_setting("sync_trakt_watched", "videolibrary"):
                sync_trakt_kodi()

                # logger.debug("Fin del hilo")

    # Si esta configurado para marcar como visto
    if config.get_setting("mark_as_watched", "videolibrary"):
        threading.Thread(target=mark_as_watched_subThread, args=[item]).start()


def sync_trakt_addon(path_folder):
    """
       Actualiza los valores de episodios vistos si
    """
    logger.info()
    # si existe el addon hacemos la busqueda
    if xbmc.getCondVisibility('System.HasAddon("script.trakt")'):
        # importamos dependencias
        paths = ["special://home/addons/script.module.dateutil/lib/", "special://home/addons/script.module.six/lib/",
                 "special://home/addons/script.module.arrow/lib/", "special://home/addons/script.module.trakt/lib/",
                 "special://home/addons/script.trakt/"]

        for path in paths:
            sys.path.append(xbmc.translatePath(path))

        # se obtiene las series vistas
        try:
            from resources.lib.traktapi import traktAPI
            traktapi = traktAPI()
        except:
            return

        shows = traktapi.getShowsWatched({})
        shows = list(shows.items())

        # obtenemos el id de la serie para comparar
        _id = re.findall("\[(.*?)\]", path_folder, flags=re.DOTALL)[0]
        logger.debug("el id es %s" % _id)

        if "tt" in _id:
            type_id = "imdb"
        elif "tvdb_" in _id:
            _id = _id.strip("tvdb_")
            type_id = "tvdb"
        elif "tmdb_" in _id:
            type_id = "tmdb"
            _id = _id.strip("tmdb_")
        else:
            logger.error("No hay _id de la serie")
            return

        # obtenemos los valores de la serie
        from core import videolibrarytools
        tvshow_file = filetools.join(path_folder, "tvshow.nfo")
        head_nfo, serie = videolibrarytools.read_nfo(tvshow_file)

        # buscamos en las series de trakt
        for show in shows:
            show_aux = show[1].to_dict()

            try:
                _id_trakt = show_aux['ids'].get(type_id, None)
                # logger.debug("ID ES %s" % _id_trakt)
                if _id_trakt:
                    if _id == _id_trakt:
                        logger.debug("ENCONTRADO!! %s" % show_aux)

                        # creamos el diccionario de trakt para la serie encontrada con el valor que tiene "visto"
                        dict_trakt_show = {}

                        for idx_season, season in enumerate(show_aux['seasons']):
                            for idx_episode, episode in enumerate(show_aux['seasons'][idx_season]['episodes']):
                                sea_epi = "%sx%s" % (show_aux['seasons'][idx_season]['number'],
                                                     str(show_aux['seasons'][idx_season]['episodes'][idx_episode][
                                                             'number']).zfill(2))

                                dict_trakt_show[sea_epi] = show_aux['seasons'][idx_season]['episodes'][idx_episode][
                                    'watched']
                        logger.debug("dict_trakt_show %s " % dict_trakt_show)

                        # obtenemos las keys que son episodios
                        regex_epi = re.compile('\d+x\d+')
                        keys_episodes = [key for key in serie.library_playcounts if regex_epi.match(key)]
                        # obtenemos las keys que son temporadas
                        keys_seasons = [key for key in serie.library_playcounts if 'season ' in key]
                        # obtenemos los numeros de las keys temporadas
                        seasons = [key.strip('season ') for key in keys_seasons]

                        # marcamos los episodios vistos
                        for k in keys_episodes:
                            serie.library_playcounts[k] = dict_trakt_show.get(k, 0)

                        for season in seasons:
                            episodios_temporada = 0
                            episodios_vistos_temporada = 0

                            # obtenemos las keys de los episodios de una determinada temporada
                            keys_season_episodes = [key for key in keys_episodes if key.startswith("%sx" % season)]

                            for k in keys_season_episodes:
                                episodios_temporada += 1
                                if serie.library_playcounts[k] > 0:
                                    episodios_vistos_temporada += 1

                            # se comprueba que si todos los episodios están vistos, se marque la temporada como vista
                            if episodios_temporada == episodios_vistos_temporada:
                                serie.library_playcounts.update({"season %s" % season: 1})

                        temporada = 0
                        temporada_vista = 0

                        for k in keys_seasons:
                            temporada += 1
                            if serie.library_playcounts[k] > 0:
                                temporada_vista += 1

                        # se comprueba que si todas las temporadas están vistas, se marque la serie como vista
                        if temporada == temporada_vista:
                            serie.library_playcounts.update({serie.title: 1})

                        logger.debug("los valores nuevos %s " % serie.library_playcounts)
                        filetools.write(tvshow_file, head_nfo + serie.tojson())

                        break
                    else:
                        continue

                else:
                    logger.error("no se ha podido obtener el id, trakt tiene: %s" % show_aux['ids'])

            except:
                import traceback
                logger.error(traceback.format_exc())


def sync_trakt_kodi(silent=True):
    # Para que la sincronizacion no sea silenciosa vale con silent=False
    if xbmc.getCondVisibility('System.HasAddon("script.trakt")'):
        notificacion = True
        if (not config.get_setting("sync_trakt_notification", "videolibrary") and
                platformtools.is_playing()):
            notificacion = False

        xbmc.executebuiltin('RunScript(script.trakt,action=sync,silent=%s)' % silent)
        logger.info("Sincronizacion con Trakt iniciada")

        if notificacion:
            platformtools.dialog_notification(config.get_localized_string(20000),
                                              config.get_localized_string(60045),
                                              icon=0,
                                              time=2000)


def mark_content_as_watched_on_kodi(item, value=1):
    """
    marca el contenido como visto o no visto en la libreria de Kodi
    @type item: item
    @param item: elemento a marcar
    @type value: int
    @param value: >0 para visto, 0 para no visto
    """
    logger.info()
    # logger.debug("item:\n" + item.tostring('\n'))
    payload_f = ''

    if item.contentType == "movie":
        movieid = 0
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies",
                   "params": {"properties": ["title", "playcount", "originaltitle", "file"]},
                   "id": 1}

        data = get_data(payload)
        if 'result' in data and "movies" in data['result']:

            if item.strm_path:              #Si Item es de un episodio
                filename = filetools.basename(item.strm_path)
                head, tail = filetools.split(filetools.split(item.strm_path)[0])
            else:                           #Si Item es de la Serie
                filename = filetools.basename(item.path)
                head, tail = filetools.split(filetools.split(item.path)[0])
            path = filetools.join(tail, filename)

            for d in data['result']['movies']:
                if d['file'].replace("/", "\\").endswith(path.replace("/", "\\")):
                    # logger.debug("marco la pelicula como vista")
                    movieid = d['movieid']
                    break

        if movieid != 0:
            payload_f = {"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {
                "movieid": movieid, "playcount": value}, "id": 1}

    else:  # item.contentType != 'movie'
        episodeid = 0
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes",
                   "params": {"properties": ["title", "playcount", "showtitle", "file", "tvshowid"]},
                   "id": 1}

        data = get_data(payload)
        if 'result' in data and "episodes" in data['result']:

            if item.strm_path:              #Si Item es de un episodio
                filename = filetools.basename(item.strm_path)
                head, tail = filetools.split(filetools.split(item.strm_path)[0])
            else:                           #Si Item es de la Serie
                filename = filetools.basename(item.path)
                head, tail = filetools.split(filetools.split(item.path)[0])
            path = filetools.join(tail, filename)

            for d in data['result']['episodes']:

                if d['file'].replace("/", "\\").endswith(path.replace("/", "\\")):
                    # logger.debug("marco el episodio como visto")
                    episodeid = d['episodeid']
                    break

        if episodeid != 0:
            payload_f = {"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {
                "episodeid": episodeid, "playcount": value}, "id": 1}

    if payload_f:
        # Marcar como visto
        data = get_data(payload_f)
        # logger.debug(str(data))
        if data['result'] != 'OK':
            logger.error("ERROR al poner el contenido como visto")


def mark_season_as_watched_on_kodi(item, value=1):
    """
        marca toda la temporada como vista o no vista en la libreria de Kodi
        @type item: item
        @param item: elemento a marcar
        @type value: int
        @param value: >0 para visto, 0 para no visto
        """
    logger.info()
    # logger.debug("item:\n" + item.tostring('\n'))

    # Solo podemos marcar la temporada como vista en la BBDD de Kodi si la BBDD es local,
    # en caso de compartir BBDD esta funcionalidad no funcionara
    if config.get_setting("db_mode", "videolibrary"):
        return

    if value == 0:
        value = 'Null'

    request_season = ''
    if item.contentSeason > -1:
        request_season = ' and c12= %s' % item.contentSeason

    tvshows_path = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_tvshows"))
    item_path1 = "%" + item.path.replace("\\\\", "\\").replace(tvshows_path, "")
    if item_path1[:-1] != "\\":
        item_path1 += "\\"
    item_path2 = item_path1.replace("\\", "/")

    sql = 'update files set playCount= %s where idFile  in ' \
          '(select idfile from episode_view where (strPath like "%s" or strPath like "%s")%s)' % \
          (value, item_path1, item_path2, request_season)

    execute_sql_kodi(sql)


def mark_content_as_watched_on_alfa(path):
    from specials import videolibrary
    from core import videolibrarytools
    
    """
        marca toda la serie o película como vista o no vista en la Videoteca de Alfa basado en su estado en la Videoteca de Kodi
        @type str: path
        @param path: carpeta de contenido a marcar
        """
    logger.info()
    #logger.debug("path: " + path)
    
    FOLDER_MOVIES = config.get_setting("folder_movies")
    FOLDER_TVSHOWS = config.get_setting("folder_tvshows")
    VIDEOLIBRARY_PATH = config.get_videolibrary_config_path()
    if not VIDEOLIBRARY_PATH:
        return

    # Solo podemos marcar el contenido como vista en la BBDD de Kodi si la BBDD es local,
    # en caso de compartir BBDD esta funcionalidad no funcionara
    #if config.get_setting("db_mode", "videolibrary"):
    #    return
    
    path2 = ''
    if "special://" in VIDEOLIBRARY_PATH:
        if FOLDER_TVSHOWS in path:
            path2 = re. sub(r'.*?%s' % FOLDER_TVSHOWS, VIDEOLIBRARY_PATH + "/" + FOLDER_TVSHOWS, path).replace("\\", "/")
        if FOLDER_MOVIES in path:
            path2 = re. sub(r'.*?%s' % FOLDER_MOVIES, VIDEOLIBRARY_PATH + "/" + FOLDER_MOVIES, path).replace("\\", "/")

    if "\\" in path:
        path = path.replace("/", "\\")
    head_nfo, item = videolibrarytools.read_nfo(path)                   #Leo el .nfo del contenido
    if not item:
        logger.error('.NFO no encontrado: ' + path)
        return

    if FOLDER_TVSHOWS in path:                                          #Compruebo si es CINE o SERIE
        contentType = "episode_view"                                    #Marco la tabla de BBDD de Kodi Video
        nfo_name = "tvshow.nfo"                                         #Construyo el nombre del .nfo
        path1 = path.replace("\\\\", "\\").replace(nfo_name, '')        #para la SQL solo necesito la carpeta
        if not path2:
            path2 = path1.replace("\\", "/")                            #Formato no Windows
        else:
            path2 = path2.replace(nfo_name, '')
        
    else:
        contentType = "movie_view"                                      #Marco la tabla de BBDD de Kodi Video
        path1 = path.replace("\\\\", "\\")                              #Formato Windows
        if not path2:
            path2 = path1.replace("\\", "/")                            #Formato no Windows
        nfo_name = scrapertools.find_single_match(path2, '\]\/(.*?)$')  #Construyo el nombre del .nfo
        path1 = path1.replace(nfo_name, '')                             #para la SQL solo necesito la carpeta
        path2 = path2.replace(nfo_name, '')                             #para la SQL solo necesito la carpeta
    path2 = filetools.remove_smb_credential(path2)                      #Si el archivo está en un servidor SMB, quitamos las credenciales
    
    #Ejecutmos la sentencia SQL
    sql = 'select strFileName, playCount from %s where (strPath like "%s" or strPath like "%s")' % (contentType, path1, path2)
    nun_records = 0
    records = None
    nun_records, records = execute_sql_kodi(sql)                        #ejecución de la SQL
    if nun_records == 0:                                                #hay error?
        logger.error("Error en la SQL: " + sql + ": 0 registros")
        return                                                          #salimos: o no está catalogado en Kodi, o hay un error en la SQL
    
    for title, playCount in records:                                    #Ahora recorremos todos los registros obtenidos
        if contentType == "episode_view":
            title_plain = title.replace('.strm', '')                    #Si es Serie, quitamos el sufijo .strm
        else:
            title_plain = scrapertools.find_single_match(item.strm_path, '.(.*?\s\[.*?\])') #si es peli, quitamos el título
        if playCount is None or playCount == 0:                         #todavía no se ha visto, lo ponemos a 0
            playCount_final = 0
        elif playCount >= 1:
            playCount_final = 1

        elif not PY3 and isinstance(title_plain, (str, unicode)):
            title_plain = title_plain.decode("utf-8").encode("utf-8")   #Hacemos esto porque si no genera esto: u'title_plain'
        elif PY3 and isinstance(var, bytes):
            title_plain = title_plain.decode('utf-8')
        item.library_playcounts.update({title_plain: playCount_final})  #actualizamos el playCount del .nfo

    if item.infoLabels['mediatype'] == "tvshow":                        #Actualizamos los playCounts de temporadas y Serie
        for season in item.library_playcounts:
            if "season" in season:                                      #buscamos las etiquetas "season" dentro de playCounts
                season_num = int(scrapertools.find_single_match(season, 'season (\d+)'))    #salvamos el núm, de Temporada
                item = videolibrary.check_season_playcount(item, season_num)    #llamamos al método que actualiza Temps. y Series

    filetools.write(path, head_nfo + item.tojson())
    
    #logger.debug(item)
    
    
def get_data(payload):
    """
    obtiene la información de la llamada JSON-RPC con la información pasada en payload
    @type payload: dict
    @param payload: data
    :return:
    """
    import urllib.request, urllib.error
    logger.info("payload: %s" % payload)
    # Required header for XBMC JSON-RPC calls, otherwise you'll get a 415 HTTP response code - Unsupported media type
    headers = {'content-type': 'application/json'}

    if config.get_setting("db_mode", "videolibrary"):
        try:
            try:
                xbmc_port = config.get_setting("xbmc_puerto", "videolibrary")
            except:
                xbmc_port = 0

            xbmc_json_rpc_url = "http://" + config.get_setting("xbmc_host", "videolibrary") + ":" + str(
                xbmc_port) + "/jsonrpc"
            req = urllib.request.Request(xbmc_json_rpc_url, data=jsontools.dump(payload), headers=headers)
            f = urllib.request.urlopen(req)
            response = f.read()
            f.close()

            logger.info("get_data: response %s" % response)
            data = jsontools.load(response)
        except Exception as ex:
            template = "An exception of type %s occured. Arguments:\n%r"
            message = template % (type(ex).__name__, ex.args)
            logger.error("error en xbmc_json_rpc_url: %s" % message)
            data = ["error"]
    else:
        try:
            data = jsontools.load(xbmc.executeJSONRPC(jsontools.dump(payload)))
        except Exception as ex:
            template = "An exception of type %s occured. Arguments:\n%r"
            message = template % (type(ex).__name__, ex.args)
            logger.error("error en xbmc.executeJSONRPC: %s" % message)
            data = ["error"]

    logger.info("data: %s" % data)

    return data


def update(folder_content=config.get_setting("folder_tvshows"), folder=""):
    """
    Actualiza la libreria dependiendo del tipo de contenido y la ruta que se le pase.

    @type folder_content: str
    @param folder_content: tipo de contenido para actualizar, series o peliculas
    @type folder: str
    @param folder: nombre de la carpeta a escanear.
    """
    logger.info(folder)

    payload = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.Scan",
        "id": 1
    }

    if folder:
        folder = str(folder)
        videolibrarypath = config.get_videolibrary_config_path()

        if folder.endswith('/') or folder.endswith('\\'):
            folder = folder[:-1]

        update_path = None

        if videolibrarypath.startswith("special:"):
            if videolibrarypath.endswith('/'):
                videolibrarypath = videolibrarypath[:-1]
            update_path = videolibrarypath + "/" + folder_content + "/" + folder + "/"
        else:
            #update_path = filetools.join(videolibrarypath, folder_content, folder) + "/"   # Problemas de encode en "folder"
            update_path = filetools.join(videolibrarypath, folder_content, ' ').rstrip()

        if not scrapertools.find_single_match(update_path, '(^\w+:\/\/)'):
            payload["params"] = {"directory": update_path}

    while xbmc.getCondVisibility('Library.IsScanningVideo()'):
        xbmc.sleep(500)

    data = get_data(payload)

    xbmc.executebuiltin('XBMC.ReloadSkin()')


def clean(mostrar_dialogo=False):
    """
    limpia la libreria de elementos que no existen
    @param mostrar_dialogo: muestra el cuadro de progreso mientras se limpia la videoteca
    @type mostrar_dialogo: bool
    """
    logger.info()
    payload = {"jsonrpc": "2.0", "method": "VideoLibrary.Clean", "id": 1,
               "params": {"showdialogs": mostrar_dialogo}}
    data = get_data(payload)

    if data.get('result', False) == 'OK':
        return True

    return False


def search_library_path():
    sql = 'SELECT strPath FROM path WHERE strPath LIKE "special://%/plugin.video.kod/library/" AND idParentPath ISNULL'
    nun_records, records = execute_sql_kodi(sql)
    if nun_records >= 1:
        logger.debug(records[0][0])
        return records[0][0]
    return None


def set_content(content_type, silent=False, custom=False):
    """
    Procedimiento para auto-configurar la videoteca de kodi con los valores por defecto
    @type content_type: str ('movie' o 'tvshow')
    @param content_type: tipo de contenido para configurar, series o peliculas
    """
    logger.info()
    continuar = True
    msg_text = ""
    videolibrarypath = config.get_setting("videolibrarypath")

    if content_type == 'movie':
        scraper = [config.get_localized_string(70093), config.get_localized_string(70096)]
        if not custom:
            seleccion = 0 # tmdb
        else:
            seleccion = platformtools.dialog_select(config.get_localized_string(70094), scraper)


        # Instalar The Movie Database
        if seleccion == -1 or seleccion == 0:
            if not xbmc.getCondVisibility('System.HasAddon(metadata.themoviedb.org)'):
                if not silent:
                    # Preguntar si queremos instalar metadata.themoviedb.org
                    install = platformtools.dialog_yesno(config.get_localized_string(60046))
                else:
                    install = True

                if install:
                    try:
                        # Instalar metadata.themoviedb.org
                        xbmc.executebuiltin('xbmc.installaddon(metadata.themoviedb.org)', True)
                        logger.info("Instalado el Scraper de películas de TheMovieDB")
                    except:
                        pass

                continuar = (install and xbmc.getCondVisibility('System.HasAddon(metadata.themoviedb.org)'))
                if not continuar:
                    msg_text = config.get_localized_string(60047)
            if continuar:
                xbmc.executebuiltin('xbmc.addon.opensettings(metadata.themoviedb.org)', True)

        # Instalar Universal Movie Scraper
        elif seleccion == 1:
            if continuar and not xbmc.getCondVisibility('System.HasAddon(metadata.universal)'):
                continuar = False
                if not silent:
                    # Preguntar si queremos instalar metadata.universal
                    install = platformtools.dialog_yesno(config.get_localized_string(70095))
                else:
                    install = True

                if install:
                    try:
                        xbmc.executebuiltin('xbmc.installaddon(metadata.universal)', True)
                        if xbmc.getCondVisibility('System.HasAddon(metadata.universal)'):
                            continuar = True
                    except:
                        pass

                continuar = (install and continuar)
                if not continuar:
                    msg_text = config.get_localized_string(70097)
            if continuar:
                xbmc.executebuiltin('xbmc.addon.opensettings(metadata.universal)', True)

    else:  # SERIES
        scraper = [config.get_localized_string(70098), config.get_localized_string(70093)]
        if not custom:
            seleccion = 0 # tvdb
        else:
            seleccion = platformtools.dialog_select(config.get_localized_string(70107), scraper)

        # Instalar The TVDB
        if seleccion == -1 or seleccion == 0:
            if not xbmc.getCondVisibility('System.HasAddon(metadata.tvdb.com)'):
                if not silent:
                    # Preguntar si queremos instalar metadata.tvdb.com
                    install = platformtools.dialog_yesno(config.get_localized_string(60048))
                else:
                    install = True

                if install:
                    try:
                        # Instalar metadata.tvdb.com
                        xbmc.executebuiltin('xbmc.installaddon(metadata.tvdb.com)', True)
                        logger.info("Instalado el Scraper de series de The TVDB")
                    except:
                        pass

                continuar = (install and xbmc.getCondVisibility('System.HasAddon(metadata.tvdb.com)'))
                if not continuar:
                    msg_text = config.get_localized_string(60049)
            if continuar:
                xbmc.executebuiltin('xbmc.addon.opensettings(metadata.tvdb.com)', True)

        # Instalar The Movie Database
        elif seleccion == 1:
            if continuar and not xbmc.getCondVisibility('System.HasAddon(metadata.tvshows.themoviedb.org)'):
                continuar = False
                if not silent:
                    # Preguntar si queremos instalar metadata.tvshows.themoviedb.org
                    install = platformtools.dialog_yesno(config.get_localized_string(60050))
                else:
                    install = True

                if install:
                    try:
                        # Instalar metadata.tvshows.themoviedb.org
                        xbmc.executebuiltin('xbmc.installaddon(metadata.tvshows.themoviedb.org)', True)
                        if xbmc.getCondVisibility('System.HasAddon(metadata.tvshows.themoviedb.org)'):
                            continuar = True
                    except:
                        pass

                continuar = (install and continuar)
                if not continuar:
                    msg_text = config.get_localized_string(60051)
            if continuar:
                xbmc.executebuiltin('xbmc.addon.opensettings(metadata.tvshows.themoviedb.org)', True)

    idPath = 0
    idParentPath = 0
    if continuar:
        continuar = False

        # Buscamos el idPath
        sql = 'SELECT MAX(idPath) FROM path'
        nun_records, records = execute_sql_kodi(sql)
        if nun_records == 1:
            idPath = records[0][0] + 1

        sql_videolibrarypath = videolibrarypath
        if sql_videolibrarypath.startswith("special://"):
            sql_videolibrarypath = sql_videolibrarypath.replace('/profile/', '/%/').replace('/home/userdata/', '/%/')
            sep = '/'
        elif scrapertools.find_single_match(sql_videolibrarypath, '(^\w+:\/\/)'):
            sep = '/'
        else:
            sep = os.sep

        if not sql_videolibrarypath.endswith(sep):
            sql_videolibrarypath += sep

        # Buscamos el idParentPath
        sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % sql_videolibrarypath
        nun_records, records = execute_sql_kodi(sql)
        if nun_records == 1:
            idParentPath = records[0][0]
            videolibrarypath = records[0][1][:-1]
            continuar = True
        else:
            # No existe videolibrarypath en la BD: la insertamos
            sql_videolibrarypath = videolibrarypath
            if not sql_videolibrarypath.endswith(sep):
                sql_videolibrarypath += sep

            sql = 'INSERT INTO path (idPath, strPath,  scanRecursive, useFolderNames, noUpdate, exclude) VALUES ' \
                  '(%s, "%s", 0, 0, 0, 0)' % (idPath, sql_videolibrarypath)
            nun_records, records = execute_sql_kodi(sql)
            if nun_records == 1:
                continuar = True
                idParentPath = idPath
                idPath += 1
            else:
                msg_text = config.get_localized_string(70101)

    if continuar:
        continuar = False

        # Fijamos strContent, strScraper, scanRecursive y strSettings
        if content_type == 'movie':
            strContent = 'movies'
            scanRecursive = 2147483647
            if seleccion == -1 or seleccion == 0:
                strScraper = 'metadata.themoviedb.org'
                path_settings = xbmc.translatePath("special://profile/addon_data/metadata.themoviedb.org/settings.xml")
            elif seleccion == 1: 
                strScraper = 'metadata.universal'
                path_settings = xbmc.translatePath("special://profile/addon_data/metadata.universal/settings.xml")
            if not os.path.exists(path_settings):
                logger.info("%s: %s" % (content_type, path_settings + " doesn't exist"))
                return continuar
            settings_data = filetools.read(path_settings)
            strSettings = ' '.join(settings_data.split()).replace("> <", "><")
            strSettings = strSettings.replace("\"","\'")
            strActualizar = "¿Desea configurar este Scraper en español como opción por defecto para películas?"
            if not videolibrarypath.endswith(sep):
                videolibrarypath += sep
            strPath = videolibrarypath + config.get_setting("folder_movies") + sep
        else:
            strContent = 'tvshows'
            scanRecursive = 0
            if seleccion == -1 or seleccion == 0:
                strScraper = 'metadata.tvdb.com'
                path_settings = xbmc.translatePath("special://profile/addon_data/metadata.tvdb.com/settings.xml")
            elif seleccion == 1: 
                strScraper = 'metadata.tvshows.themoviedb.org'
                path_settings = xbmc.translatePath("special://profile/addon_data/metadata.tvshows.themoviedb.org/settings.xml")
            if not os.path.exists(path_settings):
                logger.info("%s: %s" % (content_type, path_settings + " doesn't exist"))
                return continuar
            settings_data = filetools.read(path_settings)
            strSettings = ' '.join(settings_data.split()).replace("> <", "><")
            strSettings = strSettings.replace("\"","\'")
            strActualizar = "¿Desea configurar este Scraper en español como opción por defecto para series?"
            if not videolibrarypath.endswith(sep):
                videolibrarypath += sep
            strPath = videolibrarypath + config.get_setting("folder_tvshows") + sep

        logger.info("%s: %s" % (content_type, strPath))
        # Comprobamos si ya existe strPath en la BD para evitar duplicados
        sql = 'SELECT idPath FROM path where strPath="%s"' % strPath
        nun_records, records = execute_sql_kodi(sql)
        sql = ""
        if nun_records == 0:
            # Insertamos el scraper
            sql = 'INSERT INTO path (idPath, strPath, strContent, strScraper, scanRecursive, useFolderNames, ' \
                  'strSettings, noUpdate, exclude, idParentPath) VALUES (%s, "%s", "%s", "%s", %s, 0, ' \
                  '"%s", 0, 0, %s)' % (
                      idPath, strPath, strContent, strScraper, scanRecursive, strSettings, idParentPath)
        else:
            if not silent:
                # Preguntar si queremos configurar themoviedb.org como opcion por defecto
                actualizar = platformtools.dialog_yesno(config.get_localized_string(70098), strActualizar)
            else:
                actualizar = True

            if actualizar:
                # Actualizamos el scraper
                idPath = records[0][0]
                sql = 'UPDATE path SET strContent="%s", strScraper="%s", scanRecursive=%s, strSettings="%s" ' \
                      'WHERE idPath=%s' % (strContent, strScraper, scanRecursive, strSettings, idPath)

        if sql:
            nun_records, records = execute_sql_kodi(sql)
            if nun_records == 1:
                continuar = True

        if not continuar:
            msg_text = config.get_localized_string(60055)

    if not continuar:
        heading = config.get_localized_string(70102) % content_type
    elif content_type == 'tvshow' and not xbmc.getCondVisibility(
            'System.HasAddon(metadata.tvshows.themoviedb.org)'):
        heading = config.get_localized_string(70103) % content_type
        msg_text = config.get_localized_string(60058)
    else:
        heading = config.get_localized_string(70103) % content_type
        msg_text = config.get_localized_string(70104)

    logger.info("%s: %s" % (heading, msg_text))
    return continuar


def update_db(old_path, new_path, old_movies_folder, new_movies_folder, old_tvshows_folder, new_tvshows_folder, progress):
    def path_replace(path, old, new):
        if new.startswith("special://") or '://' in new: sep = '/'
        else: sep = os.sep

        path = path.replace(old,new)
        if sep == '/': path = path.replace('\\','/')
        else: path = path.replace('/','\\')

        return path

    logger.info()

    if old_path.startswith("special://") or '://' in old_path: sep = '/'
    else: sep = os.sep
    if not old_path.endswith(sep):
        old_path += sep

    # search MAIN path in the DB
    sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % old_path
    nun_records, records = execute_sql_kodi(sql)

    # change main path
    if records:
        idPath = records[0][0]
        strPath = path_replace(records[0][1], old_path, new_path)
        sql = 'UPDATE path SET strPath="%s" WHERE idPath=%s' % (strPath, idPath)
        nun_records, records = execute_sql_kodi(sql)

    p = 80
    progress.update(p, config.get_localized_string(20000), config.get_localized_string(80013))

    for OldFolder, NewFolder in [[old_movies_folder, new_movies_folder], [old_tvshows_folder, new_tvshows_folder]]:
        old = old_path + OldFolder
        if not old.endswith(sep): old += sep

        # Search Main Sub Folder
        sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % old
        nun_records, records = execute_sql_kodi(sql)

        # Change Main Sub Folder
        if records:
            for record in records:
                idPath = record[0]
                strPath = path_replace(record[1], filetools.join(old_path, OldFolder), filetools.join(new_path, NewFolder))
                sql = 'UPDATE path SET strPath="%s"WHERE idPath=%s' % (strPath, idPath)
                nun_records, records = execute_sql_kodi(sql)

        # Search if Sub Folder exixt in all paths
        old += '%'
        sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % old
        nun_records, records = execute_sql_kodi(sql)

        #Change Sub Folder in all paths
        if records:
            for record in records:
                idPath = record[0]
                strPath = path_replace(record[1], filetools.join(old_path, OldFolder), filetools.join(new_path, NewFolder))
                sql = 'UPDATE path SET strPath="%s"WHERE idPath=%s' % (strPath, idPath)
                nun_records, records = execute_sql_kodi(sql)


        if OldFolder == old_movies_folder:
            # if is Movie Folder
            # search and modify in "movie"
            sql = 'SELECT idMovie, c22 FROM movie where c22 LIKE "%s"' % old
            nun_records, records = execute_sql_kodi(sql)
            if records:
                for record in records:
                    idMovie = record[0]
                    strPath = path_replace(record[1], filetools.join(old_path, OldFolder), filetools.join(new_path, NewFolder))
                    sql = 'UPDATE movie SET c22="%s" WHERE idMovie=%s' % (strPath, idMovie)
                    nun_records, records = execute_sql_kodi(sql)
        else:
            # if is TV Show Folder
            # search and modify in "episode"
            sql = 'SELECT idEpisode, c18 FROM episode where c18 LIKE "%s"' % old
            nun_records, records = execute_sql_kodi(sql)
            if records:
                for record in records:
                    idEpisode = record[0]
                    strPath = path_replace(record[1], filetools.join(old_path, OldFolder), filetools.join(new_path, NewFolder))
                    sql = 'UPDATE episode SET c18="%s" WHERE idEpisode=%s' % (strPath, idEpisode)
                    nun_records, records = execute_sql_kodi(sql)
        p += 5
        progress.update(p, config.get_localized_string(20000), config.get_localized_string(80013))

    progress.update(100)
    xbmc.sleep(1000)
    progress.close()
    xbmc.executebuiltin('XBMC.ReloadSkin()')


def clean_db():
    logger.info()

    progress = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(80025))
    progress.update(0)

    config.set_setting('videolibrary_kodi', False)
    path = config.get_setting('videolibrarypath')

    # rename main path for search in the DB
    if path.startswith("special://") or '://' in path: sep = '/'
    else: sep = os.sep
    if not path.endswith(sep):
        path += sep

    # search main path in the DB
    sql = 'SELECT idPath FROM path where strPath LIKE "%s"' % path
    nun_records, records = execute_sql_kodi(sql)

    # delete main path
    if records:
        idPath = records[0][0]
        sql = 'DELETE from path WHERE idPath=%s' % idPath
        nun_records, records = execute_sql_kodi(sql)
    progress.update(20)

    path += '%'
    # search sub folders in the DB
    sql = 'SELECT idPath FROM path where strPath LIKE "%s"' % path
    nun_records, records = execute_sql_kodi(sql)

    # search TV shows in the DB
    sql = 'SELECT idShow FROM tvshow_view where strPath LIKE "%s"' % path
    nun_records, records_tvshow = execute_sql_kodi(sql)

    # delete sub folders and files
    if records:
        for record in records:
            idPath = record[0]
            sql = 'DELETE from path WHERE idPath=%s' % idPath
            nun_records, records = execute_sql_kodi(sql)
            sql = 'DELETE from files WHERE idPath=%s' % idPath
            nun_records, records = execute_sql_kodi(sql)
    progress.update(40)

    # delete TV shows
    if records_tvshow:
        for record in records_tvshow:
            idShow = record[0]
            sql = 'DELETE from tvshow WHERE idShow=%s' % idShow
            nun_records, records_tvshow = execute_sql_kodi(sql)
    progress.update(60)

    # search movies in the DB
    sql = 'SELECT idMovie FROM movie where c22 LIKE "%s"' % path
    nun_records, records = execute_sql_kodi(sql)
    # delete movies
    if records:
        for record in records:
            idMovie = record[0]
            sql = 'DELETE from movie WHERE idMovie=%s' % idMovie
            nun_records, records = execute_sql_kodi(sql)
    progress.update(80)

    # search episodes in the DB
    sql = 'SELECT idEpisode FROM episode where c18 LIKE "%s"' % path
    nun_records, records = execute_sql_kodi(sql)
    # delete episodes
    if records:
        for record in records:
            idEpisode = record[0]
            sql = 'DELETE from episode WHERE idEpisode=%s' % idEpisode
            nun_records, records = execute_sql_kodi(sql)
    progress.update(100)
    xbmc.sleep(1000)
    progress.close()
    xbmc.executebuiltin('XBMC.ReloadSkin()')


def execute_sql_kodi(sql):
    """
    Ejecuta la consulta sql contra la base de datos de kodi
    @param sql: Consulta sql valida
    @type sql: str
    @return: Numero de registros modificados o devueltos por la consulta
    @rtype nun_records: int
    @return: lista con el resultado de la consulta
    @rtype records: list of tuples
    """
    logger.info()
    file_db = ""
    nun_records = 0
    records = None

    # Buscamos el archivo de la BBDD de videos segun la version de kodi
    video_db = config.get_platform(True)['video_db']
    if video_db:
        file_db = filetools.join(xbmc.translatePath("special://userdata/Database"), video_db)

    # metodo alternativo para localizar la BBDD
    if not file_db or not filetools.exists(file_db):
        file_db = ""
        for f in filetools.listdir(xbmc.translatePath("special://userdata/Database")):
            path_f = filetools.join(xbmc.translatePath("special://userdata/Database"), f)

            if filetools.isfile(path_f) and f.lower().startswith('myvideos') and f.lower().endswith('.db'):
                file_db = path_f
                break

    if file_db:
        logger.info("Archivo de BD: %s" % file_db)
        conn = None
        try:
            import sqlite3
            conn = sqlite3.connect(file_db)
            cursor = conn.cursor()

            logger.info("Ejecutando sql: %s" % sql)
            cursor.execute(sql)
            conn.commit()

            records = cursor.fetchall()
            if sql.lower().startswith("select"):
                nun_records = len(records)
                if nun_records == 1 and records[0][0] is None:
                    nun_records = 0
                    records = []
            else:
                nun_records = conn.total_changes

            conn.close()
            logger.info("Consulta ejecutada. Registros: %s" % nun_records)

        except:
            logger.error("Error al ejecutar la consulta sql")
            if conn:
                conn.close()

    else:
        logger.debug("Base de datos no encontrada")

    return nun_records, records


def update_sources(new='', old=''):
    logger.info()
    if new == old: return True

    try:
        SOURCES_PATH = xbmc.translatePath("special://userdata/sources.xml")
        if filetools.isfile(SOURCES_PATH):
            xmldoc = minidom.parse(SOURCES_PATH)
        else:
            xmldoc = minidom.Document()
            source_nodes = xmldoc.createElement("sources")

            for type in ['programs', 'video', 'music', 'picture', 'files']:
                nodo_type = xmldoc.createElement(type)
                element_default = xmldoc.createElement("default")
                element_default.setAttribute("pathversion", "1")
                nodo_type.appendChild(element_default)
                source_nodes.appendChild(nodo_type)
            xmldoc.appendChild(source_nodes)

        # collect nodes
        # nodes = xmldoc.getElementsByTagName("video")
        video_node = xmldoc.childNodes[0].getElementsByTagName("video")[0]
        paths_node = video_node.getElementsByTagName("path")

        if old:
            # delete old path
            for node in paths_node:
                if node.firstChild.data == old:
                    parent = node.parentNode
                    remove = parent.parentNode
                    remove.removeChild(parent)

            # write changes
            if sys.version_info[0] >= 3: #PY3
                filetools.write(SOURCES_PATH, '\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]))
            else:
                filetools.write(SOURCES_PATH, b'\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]), vfs=False)
            logger.debug("The path %s has been removed from sources.xml" % old)

        if new:
            # create new path
            list_path = [p.firstChild.data for p in paths_node]
            if new in list_path:
                logger.info("The path %s already exists in sources.xml" % new)
                return True
            logger.info("The path %s does not exist in sources.xml" % new)

            # if the path does not exist we create one
            source_node = xmldoc.createElement("source")

            # <name> Node
            name_node = xmldoc.createElement("name")
            sep = os.sep
            if new.startswith("special://") or scrapertools.find_single_match(new, r'(^\w+:\/\/)'):
                sep = "/"
            name = new
            if new.endswith(sep):
                name = new[:-1]
            name_node.appendChild(xmldoc.createTextNode(name.rsplit(sep)[-1]))
            source_node.appendChild(name_node)

            # <path> Node
            path_node = xmldoc.createElement("path")
            path_node.setAttribute("pathversion", "1")
            path_node.appendChild(xmldoc.createTextNode(new))
            source_node.appendChild(path_node)

            # <allowsharing> Node
            allowsharing_node = xmldoc.createElement("allowsharing")
            allowsharing_node.appendChild(xmldoc.createTextNode('true'))
            source_node.appendChild(allowsharing_node)

            # Añadimos <source>  a <video>
            video_node.appendChild(source_node)

            # write changes
            if sys.version_info[0] >= 3: #PY3
                filetools.write(SOURCES_PATH, '\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]))
            else:
                filetools.write(SOURCES_PATH, b'\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]), vfs=False)
            logger.debug("The path %s has been added to sources.xml" % new)
        return True
    except:
        logger.debug("An error occurred. The path %s has not been added/updated to sources.xml" % old)
        return False


def ask_set_content(silent=False):
    logger.info()
    logger.debug("videolibrary_kodi %s" % config.get_setting("videolibrary_kodi"))

    def do_config(custom=False):
        if set_content("movie", True, custom) and set_content("tvshow", True, custom) and \
                       update_sources(config.get_setting("videolibrarypath")) and \
                       update_sources(config.get_setting("downloadpath")):
            platformtools.dialog_ok(config.get_localized_string(80026), config.get_localized_string(70104))
            config.set_setting("videolibrary_kodi", True)
            update()
        else:
            platformtools.dialog_ok(config.get_localized_string(80026), config.get_localized_string(80024))
            config.set_setting("videolibrary_kodi", False)

    if not silent:
        if platformtools.dialog_yesno(config.get_localized_string(20000), config.get_localized_string(80015)):
            if not platformtools.dialog_yesno(config.get_localized_string(80026), config.get_localized_string(80016), "", "", config.get_localized_string(80017), config.get_localized_string(80018)):
                path = platformtools.dialog_browse(3, config.get_localized_string(80019), config.get_setting("videolibrarypath"))
                if path != "":
                    config.set_setting("videolibrarypath", path)
                folder = platformtools.dialog_input(config.get_setting("folder_movies"), config.get_localized_string(80020))
                if folder != "":
                    config.set_setting("folder_movies", folder)
                folder = platformtools.dialog_input(config.get_setting("folder_tvshows"), config.get_localized_string(80021))
                if folder != "":
                    config.set_setting("folder_tvshows", folder)
                config.verify_directories_created()
                do_config(True)
            else:
                platformtools.dialog_ok(config.get_localized_string(80026), config.get_localized_string(80027))
                do_config(False)
        else:
            # no hemos aceptado
            platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(80022))
            config.set_setting("videolibrary_kodi", False)

    else:
        platformtools.dialog_ok(config.get_localized_string(80026), config.get_localized_string(80023))
        do_config(True)