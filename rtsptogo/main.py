import sys
import signal
import time
from threading import Thread
from wsgiref.simple_server import make_server, WSGIServer
from SocketServer import ThreadingMixIn

import rtsptogo.config
from rtsptogo.web_app import app
from rtsptogo.rtspd import RSTPServer, RSTPHandler

rtspd_server = None
httpd_server = None

def start_rtspd(host, port):
    global rtspd_server
    rtspd_server = RSTPServer((host, port), RSTPHandler)
    th = Thread(target=rtspd_server.serve_forever)
    th.start()

def start_httpd(host, port):
    global httpd_server
    class ThreaddedWSGIServer(ThreadingMixIn, WSGIServer):
        pass
    httpd_server = make_server(host, port, app, server_class=ThreaddedWSGIServer)
    th = Thread(target=httpd_server.serve_forever)
    th.start()

def handler(signum, frame):
    stop()

def stop():
    print 'Shutting Down'
    if rtspd_server:
        print 'Shutdown rtspd'
        rtspd_server.shutdown()
    if httpd_server:
        print 'Shutdown httpd'
        httpd_server.shutdown()
    print 'Shutting main thread'
    sys.exit()

def usage():
    pass

def main(argv):
    rtsptogo.config.load_config()
    config = rtsptogo.config.config
    bind_address = config.get('main', 'bind_address')
    start_rtspd(bind_address, int(config.get('main', 'rtsp_port')))
    start_httpd(bind_address, int(config.get('main', 'http_port')))
    signal.signal(signal.SIGTERM, handler)

if __name__ == '__main__':
    main(sys.argv)
    while True:
        try:
            time.sleep(1000)
        except KeyboardInterrupt:
            stop()
        except:
            pass

