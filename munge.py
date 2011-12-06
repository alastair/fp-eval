class Munge(object):
    pass

class NoMunge(Munge):
    """ No Munge """
    pass

class YouTube(Munge):
    """ Reduce quality to a standard 240p youtube quality """
    pass

class Radio(Munge):
    """ Various radio stuff """
    pass

class Bitrate(Munge):
    """ Re-encode as MP3 with a different bitrate """
    pass

class GSM(Munge):
    """ GSM Reduction """
    pass

class Noise(Munge):
    """ Random noise (white) """
    pass

class SoundMix(Munge):
    """ Mix in some other noises """
    pass
