
munge_classes = {}
import os
import tempfile
import shutil
import subprocess

import log

class Munge(object):
    def extension(self):
        """Get the preferred extension for this transform"""
        return None

    def perform(self, fromfile):
        if not fromfile or not os.path.exists(fromfile):
            log.debug("Tried to munge %s but it's not there" % fromfile)
            return None
        prefext = self.extension()
        if prefext:
            ext = prefext
        else:
            ext = os.path.splitext(fromfile)[1]
        if not ext.startswith("."):
            ext = ".%s" % ext
        (handle, tofile) = tempfile.mkstemp("%s" % ext)
        os.close(handle)
        command = self.getExecCommand(fromfile, tofile)
        if command is not None:
            log.debug("performing command")
            log.debug(" ".join(command))
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.communicate()
        else:
            shutil.copyfile(fromfile, tofile)
        return tofile

    def getExecCommand(self, fromfile, tofile):
        raise NotImplementedError("must implement getExecCommand in subclass")

class NoMunge(Munge):
    """ No Munge """
    def getExecCommand(self, fromfile, tofile):
        return None
munge_classes["nomunge"] = NoMunge

class Chop(Munge):
    """ limit the start time or length """

    def __init__(self):
        raise NotImplementedError("Implement a subclass that sets start & duration")

    def getExecCommand(self, fromfile, tofile):
        start = self.start
        dur = self.duration
        command = ["ffmpeg", "-i", fromfile, "-b", "128k", "-y"]
        if start:
            command.extend(["-ss", str(start)])
        if dur:
            command.extend(["-t", str(dur)])
        command.append(tofile)
        return command

class Chop30(Chop):
    def __init__(self): pass
    start = None
    duration = 30
class Chop15(Chop):
    def __init__(self): pass
    start = None
    duration = 15
class Chop8(Chop):
    def __init__(self): pass
    start = None
    duration = 8
class Start30(Chop):
    def __init__(self): pass
    start = 30
    duration = None
class Start60(Chop):
    def __init__(self): pass
    start = 60
    duration = None
munge_classes["chop8"] = Chop8
munge_classes["chop15"] = Chop15
munge_classes["chop30"] = Chop30
munge_classes["start30"] = Start30
munge_classes["start60"] = Start60

class Bitrate(Munge):
    """ Re-encode as MP3 with a different bitrate """
    def __init__(self):
        raise NotImplementedException("Run a subclass that supplies a bitrate")
    def getExecCommand(self, fromfile, tofile):
        command = ["ffmpeg", "-i", fromfile, "-b", "%sk" % self.bitrate, "-y", tofile]
        return command

class Bitrate64(Bitrate):
    def __init__(self): pass
    bitrate = 64
class Bitrate96(Bitrate):
    def __init__(self): pass
    bitrate = 96
munge_classes["bitrate64"] = Bitrate64
munge_classes["bitrate96"] = Bitrate96

class Samplerate22(Munge):
    """ Change to 22k samplerate"""
    def getExecCommand(self, fromfile, tofile):
        command = ["ffmpeg", "-i", fromfile, "-ar", "22050", "-y", tofile]
        return command
munge_classes["sample22"] = Samplerate22

class Mono(Munge):
    """ Change from stereo to mono """
    def getExecCommand(self, fromfile, tofile):
        command = ["ffmpeg", "-i", fromfile, "-ac", "1", "-y", tofile]
        return command
munge_classes["mono"] = Mono

class GSM(Munge):
    """ GSM Reduction """
    def extension(self):
        return "wav"
    def getExecCommand(self, fromfile, tofile):
        command = ["sox", fromfile, "--encoding", "gsm-full-rate", tofile]
        return command
munge_classes["gsm"] = GSM

class SoundMix(Munge):
    """ Mix in some other noises """
    def __init__(self):
        raise NotImplementedException("Run a subclass that supplies a noisefile")

    def getExecCommand(self, fromfile, tofile):
        pass

class WhiteNoiseMix(SoundMix):
    def __init__(self): pass
    pass
class CarNoiseMix(SoundMix):
    def __init__(self): pass
    pass
class PersonNoiseMix(SoundMix):
    def __init__(self): pass
    pass
#munge_classes["whitenoise"] = WhiteNoiseMix
#munge_classes["carnoise"] = CarNoiseMix
#munge_classes["personnoise"] = PersonNoiseMix

class Volume(Munge):
    """ Change the volume """
    def __init__(self):
        raise NotImplementedException("Run a subclass that supplies a volume")

    def getExecCommand(self, fromfile, tofile):
        command = ["sox", "-v", "%s" % self.volume, fromfile, tofile]
        return command

class Volume50(Volume):
    def __init__(self): pass
    volume = 0.5
class Volume80(Volume):
    def __init__(self): pass
    volume = 0.8
class Volume120(Volume):
    def __init__(self): pass
    volume = 1.2
munge_classes["volume50"] = Volume50
munge_classes["volume80"] = Volume80
munge_classes["volume120"] = Volume120

class Lowpass(Munge):
    """ Low pass filter """
    pass
    # lame --lowpass
#munge_classes["lowpass"] = Lowpass

class Compress(Munge):
    """ Add compression """
    pass
#munge_classes["compress"] = Compress

class EQ(Munge):
    """ Perform equalisation """
    pass
#munge_classes["eq"] = EQ

class FMFilter(Munge):
    """ Similar bandwidth and filters as what comes out of
    the radio """
    def extension(self):
        return "wav"
    def getExecCommand(self, fromfile, tofile):
        command = ["sox", fromfile, "gain", "-3", "sinc", "8000-", "29", "100", "mcompand",
                   "0.005,0.1 -47,-40,-34,-34,-17,-33", "100",
                   "0.003,0.05 -47,-40,-34,-34,-17,-33", "400",
                   "0.000625,0.0125 -47,-40,-34,-34,-15,-33", "1600",
                   "0.0001,0.025 -47,-40,-34,-34,-31,-31,-0,-30", "6400",
                   "0,0.025 -38,-31,-28,-28,-0,-25",
                   "gain", "15", "highpass", "22", "highpass", "22", "sinc", "-n", "255", "-b", "16", "-17500",
                   "gain", "9", "lowpass", "-1", "17801", tofile
                ]
        return command
    """
                     play track1.wav gain -3 sinc 8000- 29 100 mcompand \
                   "0.005,0.1 -47,-40,-34,-34,-17,-33" 100 \
                   "0.003,0.05 -47,-40,-34,-34,-17,-33" 400 \
                   "0.000625,0.0125 -47,-40,-34,-34,-15,-33" 1600 \
                   "0.0001,0.025 -47,-40,-34,-34,-31,-31,-0,-30" 6400 \
                   "0,0.025 -38,-31,-28,-28,-0,-25" \
                   gain 15 highpass 22 highpass 22 sinc -n 255 -b 16 -17500 \
                   gain 9 lowpass -1 17801

              The  audio  file  is  played with a simulated FM radio sound (or
              broadcast signal condition if the lowpass filter at the  end  is
              skipped).
              -- sox(1)
              """
munge_classes["radio"] = FMFilter

class Speed(Munge):
    """ Change the speed and pitch """
    def __init__(self):
        raise NotImplementedException("Run a subclass that supplies a speed ratio")

    def getExecCommand(self, fromfile, tofile):
        command = ["sox", fromfile, tofile, "speed", "%s" % self.speed]
        return command

class SpeedUp(Speed):
    def __init__(self): pass
    speed = 1.05
class SpeedDown(Speed):
    def __init__(self): pass
    # XXX: Is this right?
    speed = 0.95
munge_classes["speedup"] = SpeedUp
munge_classes["speeddown"] = SpeedDown
