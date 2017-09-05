# File: xplane_helpers.py
# Defines Helpers

import bpy
import os
import io_xplane2blender
import datetime
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
