import socket
import threading

import zeroconf
from config import config

class TivoListener:
    def __init__(self):
        self.tivos_lock = threading.Lock()
        self.tivos = {}

    def addService(self, zc, type, alias):
        info = zc.getServiceInfo(type, alias)
        if info:
            with self.tivos_lock:
                self.tivos[alias] = {
                    'name' : alias.split('.')[0],
                    'address' : socket.inet_ntoa(info.getAddress()),
                }
            print 'Added Tivo', self.tivos[alias]
        else:
            print 'MDNS info timeout'

    def removeService(self, zc, type, alias):
        with self.tivos_lock:
            del self.tivos[alias]

    def get_tivos(self):
        with self.tivos_lock:
            tivos_copy = self.tivos.copy()
        return tivos_copy.values()

zc = None
tl = TivoListener()

def start(host):
    global zc
    zc = zeroconf.Zeroconf(host)
    zc.addServiceListener('_tivo-videos._tcp.local.', tl)

def stop():
    if zc:
        zc.close()

get_tivos = tl.get_tivos
