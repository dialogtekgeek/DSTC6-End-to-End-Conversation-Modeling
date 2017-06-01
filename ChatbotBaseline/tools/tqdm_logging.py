
import sys
import logging
from tqdm import tqdm

# create logger object
#logger = logging.getLogger("root")

# tqdm logging handler
class TqdmLoggingHandler(logging.Handler):

    def __init__ (self, level=logging.NOTSET):
        super (self.__class__, self).__init__ (level)

    def emit (self, record):
        try:
            msg = self.format (record)
            tqdm.write ('\r' + msg, file=sys.stdout)
            self.flush ()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

# obtain a logger
def setLogger(logger, logfile='', mode='w', silent=False, debug=False,
                 format="%(asctime)s %(levelname)s %(message)s"):

    #logger = logging.getLogger("root")

    if silent:
        level = logging.WARN
    else:
        level = logging.INFO

    stdhandler = TqdmLoggingHandler(level=level)
    stdhandler.setFormatter(logging.Formatter(format))
    logger.addHandler(stdhandler)

    if logfile:
        filehandler = logging.FileHandler(logfile, mode=mode)
        filehandler.setFormatter(logging.Formatter(format))
        logger.addHandler(filehandler)

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger

