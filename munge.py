
munge_classes = {}

class Munge(object):
    def perform(self, fromfile, tofile):
        raise NotImplementedError("must implement perform(self)")

class NoMunge(Munge):
    """ No Munge """
    def perform(self, fromfile, tofile):
        return tofile
munge_classes["nomunge"] = NoMunge

class YouTube(Munge):
    """ Reduce quality to a standard 240p youtube quality """
    def perform(self, fromfile, tofile):
        return tofile

class RadioFilter(Munge):
    """ Similar bandwidth and filters as what comes out of
    the radio """
    pass

class RadioSpeed(Munge):
    """ Adjust the speed and pitch of music """
    pass

class Bitrate(Munge):
    """ Re-encode as MP3 with a different bitrate """
    pass

class Lowpass(Munge):
    """ Low pass filter """
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

class Volume(Munge):
    """ Change the volume """
    pass

class Compress(Munge):
    """ Add compression """
    pass

class EQ(Munge):
    """ Perform equalisation """
    pass
