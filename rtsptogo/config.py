import ConfigParser
import os.path

config = ConfigParser.ConfigParser()

def load_config(config_files=None):
    global config
    if not config_files:
        config_files = ['/etc/rtsptogo.conf', '/usr/local/etc/rtsptogo.conf',
            os.path.expanduser('~/.rtsptogo.conf')]
    if not config.read(config_files):
        raise Exception('No config files found %r' % config_files)

    defaults = {
        'bind_address' : '',
        'http_port' : '8081',
        'rtsp_port' : '9998',
    }
    requireds = ['mak']

    for default, value in defaults.items():
        if not config.has_option('main', default):
            config.set('main', default, value)

    for required in requireds:
        if not config.has_option('main', required):
            raise Exception("Missing config value %s" % required)
