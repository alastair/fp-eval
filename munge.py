
munge_classes = {}
import os
import tempfile
import shutil
import subprocess

import log

"""
    if decoder == 'mpg123':
        cmd = ["mpg123", "-q", "-w", target]
        if start > 0: cmd.extend(["-k", str(int(start*44100 / 1152))])
        if duration > 0: cmd.extend(["-n", str(int(duration*44100 / 1152))])
        if volume > 0: cmd.extend(["-f", str(int( (float(volume)/100.0) * 32768.0 ))])
        if downsample_to_22: cmd.extend(["-2"])
        if channels < 2: cmd.extend(["-0"])
        if speed_up: cmd.extend(["-d", "2"])
        if slow_down: cmd.extend(["-h", "2"])
        cmd.append(file)
    elif decoder =="ffmpeg":
        cmd = ["ffmpeg", "-i", file, "-f", "wav", "-y"]
        if start > 0: cmd.extend(["-ss", str(start)])
        if duration > 0: cmd.extend(["-t", str(duration)])
        #if volume > 0: cmd.extend(["-vol", str(int( (float(volume)/100.0) * 32768.0 ))]
        # -vol is undocumented, but apparently 256 is "normal"
        if downsample_to_22: cmd.extend(["-ar", "22050"])
        if channels < 2: cmd.extend(["-ac", "1"])
        #if speed_up: cmd.extend(["-d", "2"])
        #if slow_down: cmd.extend(["-h", "2"])
        cmd.append(target)
    elif decoder == "mad":
        cmd = ["madplay", "-Q", "-o", "wave:%s" % target]
        if start > 0: cmd.extend(["-s", str(start)])
        if duration > 0: cmd.extend(["-t", str(duration)])
        #if volume > 0: cmd.extend(["-f", str(int( (float(volume)/100.0) * 32768.0 ))]
        # --attenuate or --amplify takes in dB -> need to convert % to db
        if downsample_to_22: cmd.extend("--downsample")
        if channels < 2: cmd.extend(["-m"])
        #if speed_up: cmd.extend(["-d", "2"])
        #if slow_down: cmd.extend(["-h", "2"])
        cmd.append(file)
    elif decoder == "sox":
        cmd = ["sox", file, target]
        if start < 0: start = 0
        cmd.extend(["trim", str(start)])
        if duration > 0: cmd.extend([str(duration)])
        #if volume > 0: cmd.extend()
        if downsample_to_22: cmd.extend(["rate", "22050"])
        if channels < 2: cmd.extend(["channels", "1"])
        if speed_up: cmd.extend(["speed", "2.0"])
        if slow_down: cmd.extend(["speed", "0.5"])
"""

class Munge(object):
    def perform(self, fromfile):
        if not fromfile or not os.path.exists(fromfile):
            log.debug("Tried to munge %s but it's not there" % fromfile)
            return None
        ext = os.path.splitext(fromfile)[1]
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
        command = ["ffmpeg", "-i", fromfile, "-y"]
        if start:
            command.extend(["-ss", str(start)])
        if dur:
            command.extend(["-t", str(dur)])
        command.append(tofile)
        return command

class Chop60(Chop):
    def __init__(self): pass
    start = None
    duration = 60
class Chop30(Chop):
    def __init__(self): pass
    start = None
    duration = 30
class Start30(Chop):
    def __init__(self): pass
    start = 30
    duration = None
class Start30Chop30(Chop):
    def __init__(self): pass
    start = 30
    duration = 30
class Start60Chop30(Chop):
    def __init__(self): pass
    start = 60
    duration = 30
class Start60(Chop):
    def __init__(self): pass
    start = 60
    duration = None
munge_classes["chop30"] = Chop30
munge_classes["chop60"] = Chop60
munge_classes["start30"] = Start30
munge_classes["start30chop30"] = Start30Chop30
munge_classes["start60chop30"] = Start60Chop30
munge_classes["start60"] = Start60

class Bitrate(Munge):
    """ Re-encode as MP3 with a different bitrate """
    def __init__(self):
        raise NotImplementedException("Run a subclass that supplies a bitrate")
    def getExecCommand(self, fromfile, tofile):
        return self.bitrate
class Bitrate64(Bitrate):
    def __init__(self): pass
    bitrate = 64
class Bitrate96(Bitrate):
    def __init__(self): pass
    bitrate = 96
munge_classes["bitrate64"] = Bitrate64
munge_classes["bitrate96"] = Bitrate96

class GSM(Munge):
    """ GSM Reduction """
    # sox
    pass

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
        pass

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
#munge_classes["lowpass"] = Lowpass

class Compress(Munge):
    """ Add compression """
    pass
#munge_classes["compress"] = Compress

class EQ(Munge):
    """ Perform equalisation """
    pass
#munge_classes["eq"] = EQ

class YouTube(Munge):
    """ Reduce quality to a standard 240p youtube quality """
    def getExecCommand(self, fromfile, tofile):
        return tofile
#munge_classes["youtube"] = YouTube

class FMFilter(Munge):
    """ Similar bandwidth and filters as what comes out of
    the radio """
    pass
#munge_classes["radio"] = RadioFilter

class FMSpeed(Munge):
    """ Adjust the speed and pitch of music """
    pass
#munge_classes["radiospeed"] = RadioSpeed
