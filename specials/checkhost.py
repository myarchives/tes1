# -*- coding: utf-8 -*-

import xbmc, xbmcgui
import xbmcaddon
import json
from platformcode import config, logger
import requests
import sys
if sys.version_info[0] >= 3:
    from lib.httplib2 import py3 as httplib2
else:
    from lib.httplib2 import py2 as httplib2
import socket

addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')
addonid = addon.getAddonInfo('id')

LIST_SITE = ['http://www.ansa.it/', 'https://www.google.it']#, 'https://www.google.com']

# lista di siti che non verranno raggiunti con i DNS del gestore

LST_SITE_CHCK_DNS = ['https://casacinema.space', 'https://documentari-streaming-da.com']
                     #'https://www.italia-film.pw', 'https://www.cb01.uno/',] # tolti

class Kdicc():

    def __init__(self, is_exit = True, check_dns = True, view_msg = True,
                 lst_urls = [], lst_site_check_dns = [], in_addon = False):

        self.ip_addr = xbmc.getIPAddress()
        self.dns = [xbmc.getInfoLabel('Network.DNS1Address'),
                    xbmc.getInfoLabel('Network.DNS2Address')]
        self.check_dns = check_dns
        self.is_exit = is_exit
        self.lst_urls = lst_urls
        self.view_msg = view_msg
        self.lst_site_check_dns = lst_site_check_dns
        self.urls = []
        #logger.info("check #### INIZIO INIT#### ")

    def check_Ip(self):
        """
            controllo l'ip
            se ip_addr = 127.0.0.1 o ip_addr = '' allora il device non
            e' connesso al modem/router

            check the ip
            if ip_addr = 127.0.0.1 or ip_addr = '' then the device does not
            is connected to the modem/router

            return: bool
        """
        if self.ip_addr == '127.0.0.1' or self.ip_addr == '':
            return False
        else:
            return True


    def check_Adsl(self):
        """
            controllo se il device raggiunge i siti
        """

        urls = LIST_SITE
        r = self.rqst(urls)
        http_errr = 0
        for rslt in r:
            xbmc.log("check_Adsl rslt: %s" % rslt['code'], level=xbmc.LOGNOTICE)
            # Errno -2 potrebbe essere mancanza di connessione adsl o sito non raggiungibile....
            # anche nei casi in cui ci sia il cambio gestore.
            if rslt['code'] == '111' or '[Errno -3]' in str(rslt['code']) or 'Errno -2' in str(rslt['code']):
                http_errr +=1

        if len(LIST_SITE) == http_errr:
            return False
        else:
            return True


    def check_Dns(self):
        """
            Controllo se i DNS raggiungono certi siti
        """
        if self.lst_site_check_dns == []:
            urls = LST_SITE_CHCK_DNS
        else:
            urls = self.lst_site_check_dns

        r = self.rqst(urls)
        xbmc.log("check_Dns risultato: %s" % r, level=xbmc.LOGNOTICE)
        http_errr = 0
        for rslt in r:
            xbmc.log("check_Dns rslt: %s" % rslt['code'], level=xbmc.LOGNOTICE)
            if rslt['code'] == '111':
                http_errr +=1

        if len(LST_SITE_CHCK_DNS) == http_errr:
            return False
        else:
            return True


    def rqst(self, lst_urls):
        """
            url deve iniziare con http(s):'
            return : (esito, sito, url, code, reurl)
        """
        rslt_final = []

        if lst_urls == []:
            lst_urls = self.lst_urls

        for sito in lst_urls:
            rslt = {}
            try:
                r = requests.head(sito, allow_redirects = True)#, timeout=7) # da errore dopo l'inserimento in lib di httplib2
                if r.url.endswith('/'):
                    r.url = r.url[:-1]
                if str(sito) != str(r.url):
                    is_redirect = True
                else:
                    is_redirect = False

                rslt['code'] = r.status_code
                rslt['url'] = str(sito)
                rslt['rdrcturl'] = str(r.url)
                rslt['isRedirect'] = is_redirect
                rslt['history'] = r.history
                xbmc.log("Risultato nel try: %s" %  (r,), level=xbmc.LOGNOTICE)

            except requests.exceptions.ConnectionError as conn_errr:
                # Errno 10061 per s.o. win
                # gli Errno 10xxx e 11xxx saranno da compattare in qualche modo?
                # gli errori vengono inglobati in code = '111' in quanto in quel momento
                # non vengono raggiunti per una qualsiasi causa
                if '[Errno 111]' in str(conn_errr) or 'Errno 10060' in str(conn_errr) \
                     or 'Errno 10061' in str(conn_errr) \
                     or '[Errno 110]' in str(conn_errr) \
                     or 'ConnectTimeoutError' in str(conn_errr) \
                     or 'Errno 11002' in str(conn_errr) or 'ReadTimeout' in str(conn_errr) \
                     or 'Errno 11001' in str(conn_errr) \
                     or 'Errno -2' in str(conn_errr): # questo errore è anche nel code: -2
                    rslt['code'] = '111'
                    rslt['url'] = str(sito)
                    rslt['http_err'] = 'Connection error'
                else:
                    rslt['code'] = conn_errr
                    rslt['url'] = str(sito)
                    rslt['http_err'] = 'Connection refused'
            rslt_final.append(rslt)

        return rslt_final


    def http_Resp(self):
        rslt = {}
        for sito in self.lst_urls:
            try:
                s = httplib2.Http()
                code, resp = s.request(sito, body=None)
                if code.previous:
                    xbmc.log("r1 http_Resp: %s %s %s %s" %
                             (code.status, code.reason, code.previous['status'],
                              code.previous['-x-permanent-redirect-url']), level=xbmc.LOGNOTICE)
                    rslt['code'] = code.previous['status']
                    rslt['redirect'] = code.previous['-x-permanent-redirect-url']
                    rslt['status'] = code.status
                else:
                    rslt['code'] = code.status
            except httplib2.ServerNotFoundError as msg:
                # sia per mancanza di ADSL che per i siti non esistenti
                rslt['code'] = -2
            except socket.error as msg:
                # per siti irraggiungibili senza DNS corretti
                #[Errno 111] Connection refused
                rslt['code'] = 111
            except:
                rslt['code'] = 'Connection error'
        return rslt

    def view_Advise(self, txt = '' ):
        """
            Avviso per utente
            testConnected
        """
        ip = self.check_Ip()
        if ip:
            txt += '\nIP: %s\n' % self.ip_addr
            txt += '\nDNS: %s\n' % (self.dns)
        else:
            txt += '\nIP: %s' % self.ip_addr

        dialog = xbmcgui.Dialog()
        if config.get_setting('checkdns'):
            risposta= dialog.yesno(addonname, txt, nolabel=config.get_localized_string(707403), yeslabel=config.get_localized_string(707404))
            if risposta == False:
                config.set_setting('checkdns', False)
                dialog.textviewer(addonname+' '+config.get_localized_string(707405), config.get_localized_string(707406))
        else:
            txt = config.get_localized_string(707402)
            dialog.notification(addonname, txt, xbmcgui.NOTIFICATION_INFO, 10000)
"""
    def richiamato in launcher.py
"""
def test_conn(is_exit, check_dns, view_msg,
              lst_urls, lst_site_check_dns, in_addon):

    ktest = Kdicc(is_exit, check_dns, view_msg, lst_urls, lst_site_check_dns, in_addon)
    # se non ha l'ip lo comunico all'utente
    if not ktest.check_Ip():
        # non permetto di entrare nell'addon
        # I don't let you get into the addon
        # inserire codice lingua
        if view_msg == True:
            ktest.view_Advise(config.get_localized_string(70720))
        if ktest.is_exit == True:
            exit()
    # se non ha connessione ADSL lo comunico all'utente
    if not ktest.check_Adsl():
        if view_msg == True:
            ktest.view_Advise(config.get_localized_string(70721))
        if ktest.is_exit == True:
            exit()
    # se ha i DNS filtrati lo comunico all'utente
    if check_dns == True:
        if ktest.check_Dns():
            if not ktest.check_Dns():
                if view_msg == True:
                    ktest.view_Advise(config.get_localized_string(70722))

    xbmc.log("############ Inizio Check DNS ############", level=xbmc.LOGNOTICE)
    xbmc.log("## IP: %s" %  (ktest.ip_addr), level=xbmc.LOGNOTICE)
    xbmc.log("## DNS: %s" %  (ktest.dns), level=xbmc.LOGNOTICE)
    xbmc.log("############ Fine Check DNS ############", level=xbmc.LOGNOTICE)
    if check_dns == True:
        if ktest.check_Ip() == True and ktest.check_Adsl() == True and ktest.check_Dns() == True:
            return True
        else:
            return False
    else:
        if ktest.check_Ip() == True and ktest.check_Adsl() == True:
            return True
        else:
            return False

# def per la creazione del file channels.json
def check_channels(inutile=''):
    """
    leggo gli host dei canali dal file channels.json
    li controllo
    scrivo il file channels-test.json
    con il codice di errore e il nuovio url in caso di redirect

    gli url DEVONO avere http(s)

    Durante il controllo degli urls vengono rieffettuati
    i controlli di ip, asdl e dns.
    Questo perchè può succedere che in un qualsiasi momento
    la connessione possa avere problemi. Nel caso accada, il controllo e
    relativa scrittura del file viene interrotto con messaggio di avvertimento
    """
    logger.info()

    folderJson = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')).decode('utf-8')
    fileJson = 'channels.json'

    with open(folderJson+'/'+fileJson) as f:
        data = json.load(f)

    risultato = {}

    for chann, host in sorted(data.items()):

        ris = []
        # per avere un'idea della tempistica
        # utile solo se si controllano tutti i canali
        # per i canali con error 522 si perdono circa  40 sec...
        logger.info("check #### INIZIO #### channel - host :%s - %s " % (chann, host))

        rslt = Kdicc(lst_urls = [host]).http_Resp()

        # tutto ok
        if rslt['code'] == 200:
            risultato[chann] = host
        # redirect
        elif str(rslt['code']).startswith('3'):
            #risultato[chann] = str(rslt['code']) +' - '+ rslt['redirect'][:-1]
            if rslt['redirect'].endswith('/'):
                rslt['redirect'] = rslt['redirect'][:-1]
            risultato[chann] = rslt['redirect']
        # sito inesistente
        elif rslt['code'] == -2:
            risultato[chann] = 'Host Sconosciuto - '+ str(rslt['code']) +' - '+ host
        # sito non raggiungibile - probabili dns non settati
        elif rslt['code'] == 111:
            risultato[chann] = ['Host non raggiungibile - '+ str(rslt['code']) +' - '+ host]
        else:
            # altri tipi di errore
            #risultato[chann] = 'Errore Sconosciuto - '+str(rslt['code']) +' - '+ host
            risultato[chann] = host

        logger.info("check #### FINE #### rslt :%s  " % (rslt))

    fileJson_test = 'channels-test.json'
    # scrivo il file aggiornato
    with open(folderJson+'/'+fileJson_test, 'w') as f:
        data = json.dump(risultato, f, sort_keys=True, indent=4)
        logger.info(data)
