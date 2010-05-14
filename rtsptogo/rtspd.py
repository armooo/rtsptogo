import SocketServer
import mimetools
import uuid
import random
import urlparse
import threading
import urllib2

import rtsptogo.tivoapi as tivoapi
from rtsptogo.rtp import get_rtp
from rtsptogo.config import config

class ConnectionClosedError(Exception):
    pass

class RSTPHandler(SocketServer.StreamRequestHandler):

    def parse_request(self):
        if not self.parse_request_line():
            return False
        self.parse_headers()
        return True

    def parse_request_line(self):
        requestline = self.rfile.readline()
        print requestline

        if requestline == '':
            raise ConnectionClosedError()

        if requestline[-2:] == '\r\n':
            requestline = requestline[:-2]
        elif requestline[-1:] == '\n':
            requestline = requestline[:-1]

        words = requestline.split()
        if len(words) == 3:
            print 'got words'
            self.method, self.url, self.version = words
        else:
            self.send_error(400, 'Bad request')
            return False

        if self.version[:5] != 'RTSP/':
            self.send_error(505, 'RTSP Version not supported (%r)' % version)
            return False

        return True

    def parse_headers(self):
        print 'doing headers'
        self.headers = mimetools.Message(self.rfile, False)
        print 'headers done'

    def parse_transport_header(self):
        transportheader = self.headers.get('Transport')
        transports = []
        options = transportheader.split(',')
        for option in options:
            transport = {}
            parameters = option.split(';')
            transport['transport-spec'] = parameters[0]
            for parameter in parameters[1:]:
                values = parameter.split('=')
                if len(values) == 1:
                    transport[values[0]] = True
                else:
                    transport[values[0]] = values[1]
            transports.append(transport)
        return transports

    def build_transport_header(self, transport):
        transportheader = []
        transportheader.append(transport['transport-spec'])
        for k, v in transport.items():
            if k in ('transport-spec'):
                continue
            if v == True:
                transportheader.append(k)
            else:
                transportheader.append('%s=%s' % (k, v))
        transportheader.append('server_port=10%s' % random.randint(100, 999))
        return ';'.join(transportheader)

    def handle_one_request(self):
        if not self.parse_request():
            return

        print self.method, self.url
        print self.headers.headers

        mname = 'do_%s' % self.method
        if not hasattr(self, mname):
            self.send_error(501, "Unsupported method (%r)" % self.method)
            return
        method = getattr(self, mname)
        method()

    def handle(self):
        while True:
            try:
                self.handle_one_request()
            except ConnectionClosedError:
                break

    def send_error(self, code, message):
        print 'error: %s %s' % (code, message)
        self.send_response(code, message)

    def send_response(self, code, message):
        self.wfile.write('RTSP/1.0 %s %s\r\n' % (code, message))
        self.send_header('CSeq', self.headers.get('CSeq'))

    def send_header(self, keyword, value):
        self.wfile.write('%s: %s\r\n' % (keyword, value))

    def send_body(self, body):
        self.send_header('Content-Length', len(body))
        self.wfile.write('\r\n')
        self.wfile.write(body)

    def get_session(self):
        key = self.headers.get('session', str(uuid.uuid4()))
        return self.server.get_session(key)

    def del_sesison(self):
        key = self.headers.get('session', None)
        if key:
            self.server.del_session(key)

    def do_OPTIONS(self):
        self.send_response(200, 'OK')
        self.send_header('Public', 'DESCRIBE, SETUP, TEARDOWN, PLAY')
        self.send_body('')

    def do_DESCRIBE(self):
        if self.url.endswith('/audio') or self.url.endswith('/video'):
            self.send_error(459, 'Only Aggregate Operation Allowed')
            return

        self.send_response('200', 'OK')
        self.send_header('Content-Type', 'application/sdp')
        sdp = get_rtp().get_sdp({})
        self.send_body(sdp % self.url)

    def do_SETUP(self):
        session = self.get_session()
        print session

        if not (self.url.endswith('/audio') or self.url.endswith('/video')):
            self.send_error(459, 'Aggregate Operation Not Allowed')
            return

        transports = self.parse_transport_header()

        for transport in transports:
            if transport['transport-spec'] not in ('RTP/AVP', 'RTP/AVP/UDP'):
                continue
            if 'unicast' not in transport:
                continue
            if 'client_port' not in transport:
                continue
            break
        else:
            self.send_error(461, 'Unsupported Transport')
            return

        transportheader = self.build_transport_header(transport)

        if self.url.endswith('/audio'):
            session['audio_port'] = transport['client_port']
        elif self.url.endswith('/video'):
            session['video_port'] = transport['client_port']

        self.send_response('200', 'OK')
        self.send_header('Session', session['key'])
        self.send_header('Transport', transportheader)
        self.send_body('')

        import pprint
        pprint.pprint( transports )

    def do_PLAY(self):
        session = self.get_session()

        if self.url.endswith('/audio') or self.url.endswith('/video'):
            self.send_error(459, 'Only Aggregate Operation Allowed')
            return

        if session.get('playing', False):
            self.send_error('455', 'Method Not Valid in This State')
            return

        session['client_address'] = self.client_address[0]

        try:
            video_file = self.get_video()
        except urllib2.HTTPError, e:
            if e.code == 503:
                self.send_error(453, 'Not Enough Bandwidth')
                return
            raise

        rtp_out = get_rtp()(session, {})
        rtp_out.start()
        bg_copy = BackGroundCopy(video_file, rtp_out)
        session['threads'].append(bg_copy)
        bg_copy.start()

        session['playing'] = True

        self.send_response('200', 'OK')
        self.send_header('Session', session['key'])
        self.send_body('')

    def do_TEARDOWN(self):
        session = self.get_session()

        self.del_sesison()

        self.send_response('200', 'OK')
        self.send_body('')

    def get_video(self):
        url = urlparse.urlparse(self.url)
        host, path = url.path[1:].split('/', 1)
        path = path + '?' + url.query
        server = tivoapi.get_server(host, config.get('main', 'mak'))
        return server.get_video(path)

class RSTPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):

    allow_reuse_address = 1

    def __init__(self, address, request_handler_class):
        SocketServer.TCPServer.__init__(self, address, request_handler_class)
        self.daemon_threads = True

        self.sessions = {}

    def get_session(self, key):
        try:
            return self.sessions[key]
        except KeyError:
            session = {}
            self.sessions[key] = session
            session['key'] = key
            session['processes'] = []
            session['threads'] = []
            return session

    def del_session(self, key):
        session = self.sessions[key]
        for process in session['processes']:
            process.terminate()
        for thread in session['threads']:
            thread.die = True
        del self.sessions[key]

class BackGroundCopy(threading.Thread):
    def __init__(self, in_, out):
        threading.Thread.__init__(self)
        self.daemon = False
        self.in_ = in_
        self.out = out
        self.die = False

    def run(self):
        while not self.die:
            buf = self.in_.read(16*1024)
            if not buf:
                break
            try:
                self.out.write(buf)
            except IOError, e:
                if e.errno == 32 and self.die:
                    break
                else:
                    raise

if __name__ == '__main__':
    HOST, PORT = "", 9999
    server = RSTPServer((HOST, PORT), RSTPHandler)
    server.serve_forever()


