from sys import platform
if platform.startswith('win'):
    from winsound import PlaySound, SND_FILENAME, SND_ASYNC
else:
    from wave import open as waveOpen
from ossaudiodev import open as ossOpen
try:
    from ossaudiodev import AFMT_S16_NE
except ImportError:
    if byteorder == "little":
        AFMT_S16_NE = ossaudiodev.AFMT_S16_LE
    else:
        AFMT_S16_NE = ossaudiodev.AFMT_S16_BE

class SoundPlayer(object):
    def __init__(self):
        if platform.find("linux")> -1:
            self.dsp = ossOpen('/dev/dsp','w')
    
    def play(self, filename):
        if platform.startswith('win'):
            PlaySound(filename, SND_FILENAME|SND_ASYNC)
        else:
            s = waveOpen(filename,'rb')
            (nc,sw,fr,nf,comptype, compname) = s.getparams()
            self.dsp.setparameters(AFMT_S16_NE, nc, fr)
            data = s.readframes(nf)
            s.close()
            self.dsp.write(data)
    
    def close():
        if platform.find("linux") > -1:
            self.dsp.close()