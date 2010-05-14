"""
    Classes to represent a way to rtp stream.

    The public api is

    __init__(session, options)
        session is a dict with the clients options
        {
            'client_address' : '123.123.123.123'
            #Address to send rtp packets to
            'video_port' : '1234-1235'
            #video rtp port pair
            'audio_port' : '1236-1237'
            #audio rtp port pair
            'processes' : []
            #list of process objects doing work for this session
            #we will call terminate() on them
            'threads' : []
            #list of thread objexts doing work for this session
            #we will set die = True on each one
            #make sure your run method will stop when it is set
        }

        options will be a dict with video options
            {}

    @staticmethod
    get_sdp(options)
        options isa dict with the video options
            {}

        return as string with the sdp data with a %s for the main control
        and video and audio for the other 2 controls

    start()
        Get ready to start getting data

    write(data)
        TiVo encripted data to send
        #todo move the decription out of here
        #but now don't want to deal with the chance of deadlock
"""

import subprocess

from rtsptogo.config import config

class FFMPEG:
    def __init__(self, session, options):
        self.session = session
        self.options = options

    @staticmethod
    def get_sdp(options):
        sdp = [
            'v=0',
            'o=- 14957759905331434679 14957759905331434679 IN IP4 armooo-desktop',
            's=Unnamed',
            'i=N/A',
            'c=IN IP4 0.0.0.0',
            't=0 0',
            'a=tool:vlc 1.0.6',
            'a=charset:UTF-8',
            'a=control:%s',
            'm=video 0 RTP/AVP 96',
            'b=AS:200',
            'a=rtpmap:96 H264/90000',
            'a=fmtp:96 packetization-mode=1; sprop-parameter-sets=Z0LADZpygoP3/gDqALAgAABjQAASl0HihUs='
            ',aM4EyyA=',
            'a=control:video',
            'm=audio 0 RTP/AVP 97',
            'b=AS:24',
            'a=rtpmap:97 MPEG4-GENERIC/48000/2',
            'a=fmtp:97 profile-level-id=1;mode=AAC-hbr;sizelength=13;indexlength=3;'
            'indexdeltalength=3; config=1190',
            'a=control:audio',
        ]
        return '\n'.join(sdp)

    def start(self):
        self.tivodecode = get_tivodecode()
        self.session['processes'].append(self.tivodecode)

        ffmpeg_command = self.build_command()
        ffmpeg = subprocess.Popen(ffmpeg_command, stdin=self.tivodecode.stdout)
        self.session['processes'].append(ffmpeg)

    def write(self, data):
        self.tivodecode.stdin.write(data)

    def build_command(self):
        command = []
        command.extend('/usr/bin/ffmpeg -i -'.split())
        address = self.session['client_address']
        if 'video_port' in self.session:
            port = self.session['video_port'].split('-')[0]
            command.extend('-vglobal 1 -re -s qvga -vcodec libx264 -vpre hq ' \
                '-vpre ipod320 -crf 22 -threads 0 -vb 100k -an -f rtp'.split())
            command.append('rtp://%s:%s' % (address, port))
        if 'audio_port' in self.session:
            port = self.session['audio_port'].split('-')[0]
            command.extend('-flags +global_header -re -acodec libfaac -vn -f rtp'.split())
            command.append('rtp://%s:%s' % (address, port))
            command.append('-newaudio')

        return command

def get_rtp():
    return FFMPEG

def get_tivodecode():
        mak = config.get('main', 'mak')
        tivodecode_command = ('tivodecode -m %s -' % mak).split()
        tivodecode = subprocess.Popen(tivodecode_command, stdout=subprocess.PIPE,
            stdin=subprocess.PIPE)
        return tivodecode
