import json
import urlparse
import urllib
import sys
import os.path

import web
import rtsptogo.tivoapi as tivoapi
import rtsptogo.discover as discover
from rtsptogo.config import config

urls = (
    r'/', 'Index',
    r'/(.*?)/(.*)', 'Tivo',
)

render = web.template.render(os.path.join(os.path.dirname(__file__), 'templates'))

class Tivo:
    def GET(self, tivo_address, path):
        if not tivo_address in [t['address'] for t in discover.get_tivos()]:
            raise Exception('Bad tivo address')
        if not path:
            path = '/'
        else:
            path = '/' + path

        tivo = tivoapi.get_server(tivo_address, config.get('main', 'mak'))
        items = tivo.get_container(path)

        def patch_item(item):
            item = item.copy()
            if item['type'] == 'container':
                path = item['path']
                del item['path']
                url = 'http://%s/%s%s' % (web.ctx.env['HTTP_HOST'],
                    tivo_address, path)
                item['url'] = url

            elif item['type'] == 'video':
                hostname = web.ctx.env['HTTP_HOST'].split(':')[0]
                url = urlparse.urlparse(item['url'])
                rtsp_port = config.get('main', 'rtsp_port')
                item['url'] = 'rtsp://%s:%s/%s%s?%s' % (hostname, rtsp_port,
                    tivo_address, url.path, url.query)
            return item

        items = [patch_item(item) for item in items]

        if web.ctx.env['HTTP_ACCEPT'] == 'application/json':
            web.header('Content-Type', 'application/json')
            return json.dumps([items])
        else:
            return render.listing(items)

class Index:
    def GET(self):
        items = []
        for tivo in discover.get_tivos():
            item = {}
            items.append(item)
            item['type'] = 'tivo'
            item['title'] = tivo['name']
            item['url'] = 'http://%s/%s/NowPlaying' % \
                (web.ctx.env['HTTP_HOST'], tivo['address'])

        if web.ctx.env['HTTP_ACCEPT'] == 'application/json':
            web.header('Content-Type', 'application/json')
            return json.dumps([items])
        else:
            return render.index(items)

application = web.application(urls, globals())
application.internalerror = web.debugerror
app = application.wsgifunc()
