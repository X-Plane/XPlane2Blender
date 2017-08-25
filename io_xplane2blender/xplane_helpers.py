# File: xplane_helpers.py
# Defines Helpers

import bpy
import os
import io_xplane2blender
from . import bl_info
import datetime, time
import re
from builtins import str

FLOAT_PRECISION = 8

def floatToStr(n):
    s = '0'
    n = round(n, FLOAT_PRECISION)
    n_int = int(n)

    if n_int == n:
        s = '%d' % n_int
    else:
        s = (('%.' + str(FLOAT_PRECISION) + 'f') % n).rstrip('0')

    return s

def firstMatchInList(pattern, items):
    for i in range(0, len(items)):
        item = items[i]

        if pattern.fullmatch(item):
            return item

    return False

def getColorAndLitTextureSlots(mat):
    texture = None
    textureLit = None

    for slot in mat.texture_slots:
        if slot and slot.use and slot.texture and slot.texture.type == 'IMAGE':
            if slot.use_map_color_diffuse:
                texture = slot
            elif slot.use_map_emit:
                textureLit = slot

    return texture, textureLit

#TODO: Pretty sure Blender has an API for this in bpy.path
def resolveBlenderPath(path):
    blenddir = os.path.dirname(bpy.context.blend_data.filepath)

    if path[0:2] == '//':
        return os.path.join(blenddir, path[2:])
    else:
        return path


# Variable:
# 
# Since the build number will usually change by the second,
# it is not often useful to include the build number in comparisons.
# This can, however, be turned on as needed to debug problems
debug_include_build_number = False
    
# Class: XPlane2Blender 
#
# Contains useful methods for getting information about the
# version and build number of XPlane2Blender 
#
# Names are in the format of
# io_xplane2blender_major_minor_release(|-(alpha|beta|rc)\.([1-9]+))+(YYYYMMDDHHMMSS).zip
class XPlane2BlenderVersion():
    # Variable: xplane2blender_version
    # Tuple of Blender addon version, (major, minor, revision)
    _xplane2blender_version = (0,0,0)
    
    # Variable: _build_type
    # The type of build this is, always a value in BUILD_TYPES
    _build_type = ""
    
    # Variable: _build_type_version
    # The version of that build type, starting at 1 (except full, blank "",
    # releases which have no version
    _build_type_version = 0
    
    # Constant: BUILD_TYPES_
    # Constants for relavent build types
    BUILD_TYPES_ALPHA = "alpha"
    BUILD_TYPES_BETA  = "beta"
    BUILD_TYPES_RC    = "rc"
    BUILD_TYPES_RELEASE = ""
    
    # Constant: BUILD_TYPES
    # Types of builds available, ordered in tuple in ascending precedence
    BUILD_TYPES = (BUILD_TYPES_ALPHA, BUILD_TYPES_BETA, BUILD_TYPES_RC, BUILD_TYPES_RELEASE)
    
    # Variable:
    # If run as part of the plugin, this will be replaced
    # with the current YYYYMMSSHHMMSS from the UNIX epoch.
    # If created as a build, the build script will replace this
    # number with the YYYYMMSSHHMMSS at that point.
    __build_number = '{BUILD_NUMBER}'
    
    # __init__
    # 
    # version - Accepts a tuple in the form of (m,m,r), all ints
    # build_type - Accepts one of the types found in BUILD_TYPES ("alpha","beta","rc","")
    # build_type_version - Accepts a number >= 1
    def __init__(self, version, build_type, build_type_version):
        assert len(version) == 3
            
        #For a brief period of time, 3.2.x was known as 3.20.x.
        #When actually get to version 3.20 we'll figure something out,
        #probably related to the file creation date, use the fact that only
        #3.20.0 and 3.20.6-14 are messed up, or we'll skip entirely over it
        #straight to 3.30.0 - Ted, 8/24/2017 
        if version[1] >= 20:
            self._xplane2blender_version = (version[0],2,version[2])
        else:
            self._xplane2blender_version = version

        assert build_type in self.BUILD_TYPES
        self._build_type = build_type

        if self._build_type  == "":
            assert build_type_version == 0 
        else:
            assert build_type_version > 0

        self._build_type_version = build_type_version

        #build_number is not assigned here because it will either have been
        #written when the build script was run or generated and returned with
        #getBuildNumberStr()
        
    @property
    def xplane2blender_version(self):
        return self._xplane2blender_version
    
    def getVersionStr(self):
        return '.'.join(map(str,self.xplane2blender_version))
 
    # Method: getBuildType
    #
    # returns build type string
    @property
    def build_type(self):    
        return self._build_type
    
    # Method: getBuildTypeVersion
    #
    # returns build type version (an <Int>)
    @property
    def build_type_version(self):
        return self._build_type_version
 
    # Method: getBuildNumber
    #
    # returns build number string
    def getBuildNumberStr(self):
        # If we are using a pre-built version, use that saved version
        if self.__build_number != '{BUILD_NUMBER}':
            return self.__build_number
        else:
            #You either have a build number or you don't.
            return ''
    
    def getBuildNumberDateTime(self):
        #Use the UNIX Timestamp in UTC 
        return datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y%m%d%H%M%S")

    # Method: asFileName
    #
    # Gets the version in its filename version (all .'s replaced with version
    def asFileName(self):
        return str(self).replace('.','_')

    def __eq__(self,other):
        if isinstance(other, XPlane2BlenderVersion):
            if self.xplane2blender_version == other.xplane2blender_version:
                if self.build_type == other.build_type:
                    if self._build_type_version == other._build_type_version:
                        if debug_include_build_number and self.__build_number == other.__build_number:
                            return True

            return False
        else:
            raise NotImplemented

    def __ne__(self,other):
        return self.__eq__(other)

    def __lt__(self,other):
        if isinstance(other, XPlane2BlenderVersion):
            if self.xplane2blender_version < other.xplane2blender_version:
                return True
            elif self.BUILD_TYPES.index(self.build_type) < self.BUILD_TYPES.index(other.build_type):
                return True
            elif self._build_type_version < other._build_type_version:
                return True
            elif debug_include_build_number and self.__build_number < other.__build_number:
                return True

            return False
        else:
            raise NotImplemented

    def __gt__(self,other):
        if isinstance(other, XPlane2BlenderVersion):
            if self.xplane2blender_version > other.xplane2blender_version:
                return True
            elif self.BUILD_TYPES.index(self.build_type) > self.BUILD_TYPES.index(other.build_type):
                return True
            elif self._build_type_version > other._build_type_version:
                return True
            elif debug_include_build_number and self.__build_number > other.__build_number:
                return True

            return False
        else:
            raise NotImplemented

    def __le__(self,other):
        if isinstance(other, XPlane2BlenderVersion):
            return self < other or self == other
        
    def __ge__(self,other):
        if isinstance(other, XPlane2BlenderVersion):
            return self > other or self == other

    def __hash__(self):
        if debug_include_build_number:
            return hash((self.xplane2blender_version, self._build_type, self._build_type_version, self.__build_number))
        else:
            return hash((self.xplane2blender_version, self._build_type, self._build_type_version))
            
    def __str__(self):
        if self.build_type == '':
            return self.getVersionStr()
        else:
            return "%s%s%s.%s" % (self.getVersionStr(), '' if self.build_type == '' else '.',  self.build_type, self.build_type_version)
 
    def fullVersionStr(self):
        return "%s%s%s.%s+%s" % (self.xplane2blender_version,
                                '' if self.build_type == '' else '.',
                                self.build_type,
                                self.build_type_version,
                                'NONE' if self.getBuildNumberStr() == '' else self.getBuildNumberStr())

    @staticmethod
    def parseVersion(version_string):
        if version_string.startswith('v'):
            version_string = version_string[1:]

        #If we're going from a file name, got back to a Blender name
        version_string = version_string.replace('_','.')
        
        if '-' in version_string and '+' in version_string:
            #Group 1: Major.Minor.revision
            #Group 2: Build type (3) and literal '.' and number (4)
            #Literal +
             #Group 5: YYYYMMDDHHMMSS
            format_str = r"(\d+\.\d+\.\d+)" + \
                         r"(|-(alpha|beta|rc)\.([1-9]+))" + \
                         r"\+" + \
                         r"(\d{14})"
                         
            version_matches = re.match(format_str,version_string)
            
            if version_matches:
                version_tuple    = tuple(version_matches.group(1).split('.'))
                build_type       = "" if len(version_matches.group(2)) == 0 else version_matches.group(3)
                build_type_version   = 0 if build_type == "" else version_matches.group(4)
                build_number_str     = version_matches.group(5)
                
                #Regex groups for (hopefully matching) YYYYMMDDHHMMSS
                datetime_matches = re.match(r"(\d){4}" + \
                                            r"(\d){2}" + \
                                            r"(\d){2}" + \
                                            r"(\d){2}" + \
                                            r"(\d){2}" + \
                                            r"(\d){2}")

                datetime_groups = datetime_matches.groups[1:]
                year   = int(datetime_matches.group(1))
                month  = int(datetime_matches.group(2))
                day    = int(datetime_matches.group(3))
                hour   = int(datetime_matches.group(4))
                minute = int(datetime_matches.group(5))
                second = int(datetime_matches.group(6))
                
                # Following the dry principle, we'll just let the datetime class validate this data
                # for us
                try:
                    datetime.datetime(*datetime_groups)
                except:
                    assert False #Make sure we never reach here!
                
                return XPlane2BlenderVersion(version_tuple,build_type,build_type_version)
            else:
                return None
        else:
            #Old style without build number or types
            version_matches = re.match(r"((\d+)\.(\d+)\.(\d+))",version_string)
            assert version_matches is not None
            return XPlane2BlenderVersion((int(version_matches.groups()[1]),
                                          int(version_matches.groups()[2]),
                                          int(version_matches.groups()[3])),
                                         "",
                                         0)

#This a hack to help tests.py catch when an error is an error,
#because everybody and their pet poodle like using the words 'Fail',
#'Error', "FAIL", and "ERROR" making regex impossible.
#
#unittest prints a handy string of .'s, F's, and E's on the first line,
#but due to reasons beyond my grasp, sometimes they don't print a newline
#at the end of it when a failure occurs, making it useless, since we use the word
#"INFO" with an F, meaning you can't search the first line for an F!
#
#Hence this stupid stupid hack, which, is hopefully useful in someway
#Rather than a "did_print_once"
#
#This is yet another reminder about how relying on strings printed to a console
#To tell how your unit test went is a bad idea, epsecially when you can't seem to control
#What gets output when.
message_to_str_count = 0

class XPlaneLogger():
    def __init__(self):
        self.transports = []
        self.messages = []
        
    def addTransport(self, transport, messageTypes = ['error', 'warning', 'info', 'success']):
        self.transports.append({
            'fn': transport,
            'types': messageTypes
        })

    def clearTransports(self):
        del self.transports[:]

    def clearMessages(self):
        del self.messages[:]

    def messagesToString(self, messages = None):
        if messages == None:
            messages = self.messages

        out = ''

        for message in messages:
            out += XPlaneLogger.messageToString(message['type'], message['message'], message['context']) + '\n'

        return out

    def log(self, messageType, message, context = None):
        self.messages.append({
            'type': messageType,
            'message': message,
            'context': context
        })

        for transport in self.transports:
            if messageType in transport['types']:
                transport['fn'](messageType, message, context)

    def error(self, message, context = None):
        self.log('error', message, context)

    def warn(self, message, context = None):
        self.log('warning', message, context)

    def info(self, message, context = None):
        self.log('info', message, context)

    def success(self, message, context = None):
        self.log('success', message, context)

    def findOfType(self, messageType):
        messages = []

        for message in self.messages:
            if message['type'] == messageType:
                messages.append(message)

        return messages

    def hasOfType(self, messageType):
        for message in self.messages:
            if message['type'] == messageType:
                return True

        return False

    def findErrors(self):
        return self.findOfType('error')

    def hasErrors(self):
        return self.hasOfType('error')

    def findWarnings(self):
        return self.findOfType('warning')

    def hasWarnings(self):
        return self.hasOfType('warning')

    def findInfos(self):
        return self.findOfType('info')
    
    @staticmethod
    def messageToString(messageType, message, context = None):
        io_xplane2blender.xplane_helpers.message_to_str_count += 1
        return '%s: %s' % (messageType.upper(), message)

    @staticmethod
    def InternalTextTransport(name = 'XPlane2Blender.log'):
        if bpy.data.texts.find(name) == -1:
            log = bpy.data.texts.new(name)
        else:
            log = bpy.data.texts[name]

        log.clear()

        def transport(messageType, message, context = None):
            log.write(XPlaneLogger.messageToString(messageType, message, context) + '\n')

        return transport

    @staticmethod
    def ConsoleTransport():
        def transport(messageType, message, context = None):
            if io_xplane2blender.xplane_helpers.message_to_str_count == 1:
                print('\n')
            print(XPlaneLogger.messageToString(messageType, message, context))

        return transport

    @staticmethod
    def FileTransport(filehandle):
        def transport(messageType, message, context = None):
            filehandle.write(XPlaneLogger.messageToString(messageType, message, context) + '\n')

        return transport

# Class: XPlaneDebugger
# Prints debugging information and optionally logs them to a file.
class XPlaneDebugger():
    # Property: log
    # bool - Set to True to enable logfile. Default is False.
    log = False

    # Constructor: __init__
    def __init__(self):
        pass

    # Method: start
    # Starts the debugger and creates a log file, if logging is enabled.
    #
    # Parameters:
    #   bool log - Set True if log file should be written, else False
    def start(self, log):
        import time
        import os
        import bpy
#        import sys
#        import logging

        self.log = log

        if self.log:
            (name, ext) = os.path.splitext(bpy.context.blend_data.filepath)
            dir = os.path.dirname(bpy.context.blend_data.filepath)
            self.logfile = os.path.join(dir,name+'_'+time.strftime("%y-%m-%d-%H-%M-%S")+'_xplane2blender.log')

            # touch the file
            file = open(self.logfile,"w")
            file.close()

#            self.excepthook = sys.excepthook
#            sys.excepthook = self.exception
#            self.logger = logging.getLogger()
#            self.streamHandler = logging.StreamHandler()
#            self.fileHandler = logging.FileHandler(self.logfile)
#            self.logger.addHandler(self.streamHandler)

    # Method: write
    # Writes a message to the logfile.
    #
    # Parameters:
    #   string msg - The message to write.
    def write(self, msg):
        file = open(self.logfile, "a")
        #file.seek(1,os.SEEK_END)
        file.write(msg)
        file.close()

    # Method: debug
    # Prints out a message and also writes it to the logfile if logging is enabled.
    #
    # Parameters:
    #   string msg - The message to output.
    def debug(self, msg):
        print(msg)
        if self.log:
            self.write(msg + "\n")

    # Method: exception
    # Experimental exception handler. Not working yet.
    def exception(self, type, value, traceback):
        o = "Exception: " + type + "\n"
        o += "\t" + value + "\n"
        o += "\tTraceback: " + str(traceback)+"\n"
        self.write(o)

    # Method: end
    # Ends the debugging session.
    def end(self):
        self.log = False
#        sys.excepthook = self.excepthook

# Class: XPlaneProfiler
# Stores profiling information of processes.
class XPlaneProfiler():
    # Property: times
    # dict of stored times used internally.
    times = {}

    # Constructor: __init__
    def __init__(self):
        self.times = {}

    # Method: def
    # Starts profiling of a process. If the process has already started profiling, the process counter will be increased.
    #
    # Parameters:
    #   string name - Name of the process.
    def start(self,name):
        from time import time

        if name in self.times:
            if self.times[name][3]:
                self.times[name][0] = time()
                self.times[name][3] = False

            self.times[name][2]+=1
        else:
            self.times[name] = [time(),0.0,1,False]

    # Method: end
    # Ends profiling of a process.
    #
    # Parameters:
    #   string name - Name of the process.
    def end(self,name):
        from time import time

        if name in self.times:
            self.times[name][1]+=time()-self.times[name][0]
            self.times[name][3] = True

    # Method: getTime
    # Returns the time and call number for a process.
    #
    # Parameters:
    #   string name - Name of the process.
    #
    # Returns:
    #   string - Information about the the process.
    def getTime(self,name):
        return '%s: %6.6f sec (calls: %d)' % (name,self.times[name][1],self.times[name][2])

    # Method: getTimes
    # Returns the times and call numbers of all processes. Uses <getTime> internally.
    #
    # Returns:
    #   string - Information about the processes.
    def getTimes(self):
        _times = ''
        for name in self.times:
            _times+=self.getTime(name)+"\n"

        return _times


logger = XPlaneLogger()
