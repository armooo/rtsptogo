import json
import urlparse
import urllib
import sys
import os.path

import web
import tivoapi

MAC = ''
TIVOS = ['192.168.100.217', '192.168.100.231']

urls = (
    r'/', 'Index',
    r'/(.*?)/(.*)', 'Tivo',
)

render = web.template.render(os.path.join(os.path.dirname(__file__), 'templates'))

class Tivo:
    def GET(self, tivo_address, path):
        if not tivo_address in TIVOS:
            raise Exception('Bad tivo address')
        if not path:
            path = '/'
        else:
            path = '/' + path

        tivo = tivoapi.Server(tivo_address, MAC)
        items = tivo.get_container(path)

        def patch_item(item):
            item = item.copy()
            if item['type'] == 'container':
                path = item['path']
                del item['path']
                url = 'http://%s/%s%s' % (web.ctx.env['HTTP_HOST'], tivo_address, path)
                item['url'] = url

            elif item['type'] == 'video':
                hostname = web.ctx.env['HTTP_HOST'].split(':')[0]
                url = urlparse.urlparse(item['url'])
                item['url'] = 'rtsp://%s:9999/%s%s?%s' % (hostname, tivo_address, url.path, url.query)
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
        for address in TIVOS:
            item = {}
            items.append(item)
            item['type'] = 'tivo'
            item['title'] = address
            item['url'] = 'http://%s/%s/NowPlaying' % (web.ctx.env['HTTP_HOST'], address)

        if web.ctx.env['HTTP_ACCEPT'] == 'application/json':
            web.header('Content-Type', 'application/json')
            return json.dumps([items])
        else:
            return render.listing(items)

application = web.application(urls, globals())
application.internalerror = web.debugerror
app = application.wsgifunc()
