import urllib
import urllib2
import urlparse
import cgi
import cookielib
import xml.etree.ElementTree as ElementTree

class Server:
    API_PATH = '/TiVoConnect'
    NS_CALYPSO = '{http://www.tivo.com/developer/calypso-protocol-1.6/}'
    TYPE_VIDEO = 'video/'
    TYPE_CONTAINER = 'x-tivo-container/'
    cache = {}

    def __init__(self, address, mak):
        self.address = address

        pass_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pass_mgr.add_password('TiVo DVR', address, 'tivo', mak)
        authhandler = urllib2.HTTPDigestAuthHandler(pass_mgr)
        cj = cookielib.CookieJar()
        cookiehandler = urllib2.HTTPCookieProcessor(cj)
        self.opener = urllib2.build_opener(authhandler, cookiehandler)

    def get_container(self, path):
        time_stamp, data = self.cache.get((self.address, path), (None, None))
        if time_stamp:
            summery = self.get('QueryContainer', Container=path, ItemCount=0)
            current_time_stamp = summery.findtext(self.NS_CALYPSO+'Details/'+self.NS_CALYPSO+'LastChangeDate')
            if current_time_stamp and current_time_stamp == time_stamp:
                return data

        xml = self.get('QueryContainer', Container=path)
        current_time_stamp = xml.findtext(self.NS_CALYPSO+'Details/'+self.NS_CALYPSO+'LastChangeDate')

        data = [self._convert_item(item) for item in xml.findall(self.NS_CALYPSO+'Item')]
        self.cache[(self.address, path)] = (current_time_stamp, data)
        return data

    def get_video(self, path):
        url = 'http://%s/%s' % (self.address, path)
        print '!'*5, url
        return self.opener.open(url)

    def _convert_item(self, xml):
        item = {}
        details = xml.find(self.NS_CALYPSO+'Details')

        title = details.findtext(self.NS_CALYPSO+'Title')
        item['title'] = title
        type = details.findtext(self.NS_CALYPSO+'ContentType')

        if type.startswith(self.TYPE_VIDEO):
            item['type'] = 'video'
            duration = details.findtext(self.NS_CALYPSO+'Duration')
            item['duration'] = duration
            episode_title = details.findtext(self.NS_CALYPSO+'EpisodeTitle')
            item['episode_title'] = episode_title
            description = details.findtext(self.NS_CALYPSO+'Description')
            item['description'] = description
            url = xml.findtext(self.NS_CALYPSO+'Links/'+self.NS_CALYPSO+'Content/'+self.NS_CALYPSO+'Url')
            item['url'] = url

        elif type.startswith(self.TYPE_CONTAINER):
            item['type'] = 'container'
            total_items = details.findtext(self.NS_CALYPSO+'TotalItems')
            item['total_items'] = total_items

            url = xml.findtext(self.NS_CALYPSO+'Links/'+self.NS_CALYPSO+'Content/'+self.NS_CALYPSO+'Url')
            query = urlparse.urlparse(url).query
            item['path'] = cgi.parse_qs(query)['Container'][0]

        return item


    def get(self, command, **kargs):
        url = ['https://', self.address, self.API_PATH , '?']
        kargs['Command'] = command
        url.append(urllib.urlencode(kargs))

        return ElementTree.fromstring(self.opener.open(''.join(url)).read())

_servers = {}

def get_server(address, mak):
    try:
        return _servers[(address, mak)]
    except KeyError:
        server = Server(address, mak)
        _servers[(address, mak)] = server
        return server

