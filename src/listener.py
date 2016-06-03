import bluetooth
import signal
import time
import re
import threading
import select
import logging

from threading import Timer

import sync
import command

from util import *

class Listener (threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock  = sock
        self.ready = select.select([sock], [], [], 1)
        self.pendingMsg = ''
        self.running = False
        self.alive = True   
        self.watchdog = Timer(1.0, self.die)     
        self.watchdog.start()

    def readSock(self):
        resp = self.pendingMsg
        while not sync.terminate.isSet():
            pos = resp.find('\n')
            if pos > 0:
                if pos == len(resp) - 1:
                    self.pendingMsg = ''
                    return resp.strip()
                else:
                    prefix = resp[0:pos]
                    self.pendingMsg = resp[pos+1:]
                    return prefix.strip()
            try:
                data = self.sock.recv(1024)
            except:
                time.sleep(0.001)
                continue
            resp += data
        return None

    def dummyRead(self):
        time.sleep(0.5)
        return 'RUN OK'

    def live(self):
        self.alive = True

    def die(self):
        if not self.running:
            # avoid suicide before start
            self.watchdog = Timer(0.5, self.die)
            self.watchdog.start()
            return
        if self.alive:
            # see if someone will claim we are alive in the next second or so
            self.alive = False
            self.watchdog = Timer(0.5, self.die)
            self.watchdog.start()
        else:
            # ok, no one claimed we are alive, so we are probably dead
            cmd = (command.TRG_OFF, None)
            sync.putCommand(cmd)
            sync.disconnect.set()
            print "I'm dead :-("            

    def run(self):
        print "starting bluetooth listener"
        while not sync.terminate.isSet():
            msg = self.readSock()
            if msg is None:
                continue
            logging.debug("bluetooth message: %s" % msg)
            self.live()
            if msg == 'RUN OK':
                self.running = True
                sync.runOK.set()
                continue
            if msg == 'STP OK':
                self.running = False
                sync.stopOK.set()
                continue
            if msg == 'RST OK':
                sync.resetOK.set()
                continue
            if msg == 'CAL OK':
                sync.calibrateOK.set()
                continue
            if msg == 'TRG ON':
                cmd = (command.TRG_ON, None)
                sync.putCommand(cmd)
                continue
            if msg == 'TRG OFF':
                cmd = (command.TRG_OFF, None)
                sync.putCommand(cmd)
                continue            
            if msg == 'RFI ON':            
                cmd = (command.RFI_ON, None)
                sync.putCommand(cmd)
                continue
            if msg == 'RFI OFF':            
                cmd = (command.RFI_OFF, None)
                sync.putCommand(cmd)
                continue
            m = re.search('POS (-?\d+\.\d+),(-?\d+\.\d+),(-?\d+\.\d+)', msg)
            if m:
                x = -float(m.group(3)); # FIXME: changed order of readings
                y = float(m.group(1));
                z = float(m.group(2));
                cmd = (command.SET_POS, (x,y,z))
                sync.putCommand(cmd)
                continue
            logging.warning("illegal message  '%s'" % msg)
        print "stopping bluetooth listener"
