import threading
import Queue
import logging
import command

#class Sync:
 
resetOK     = threading.Event()
stopOK      = threading.Event()
runOK       = threading.Event()
calibrateOK = threading.Event()
terminate   = threading.Event()
disconnect  = threading.Event()
queueEvent  = threading.Event()

qLock       = threading.Lock()
queue       = Queue.Queue(100)

def putCommand(cmd):
    qLock.acquire()
    queue.put(cmd)
    logging.debug("send command %s" % command.cmd2str(cmd))
    qLock.release()
    queueEvent.set()
