from enum import IntEnum
import time

class LogLevel(IntEnum):

  CRITICAL = 0
  ERROR = 1
  WARNING = 2
  INFO = 3
  DEBUG = 4
  ANY = 5

class Logger():

    def __init__(self, log_level, message_sep=': '):
        self.log_level = log_level
        self.message_sep = message_sep

    def log(self, log_level, *messages):
        """Print messages at the given log level, if it is within this object's
        specified log level.
    
        Args:
            level: LogLevel enum selection of this message
            *messages: unnamed args that will be concatenated as the message
        Returns:
            None
        """
        if log_level <= self.log_level:
            time_stamp = time.strftime('%Y-%m-%d %H:%M:%S')
            message = self.message_sep.join(messages)
            print('%s (%s) %s' % (log_level.name, time_stamp, message))

    def critical(self, *messages):
        self.log(LogLevel.CRITICAL, *messages)
    
    def error(self, *messages):
        self.log(LogLevel.ERROR, *messages)
    
    def warning(self, *messages):
        self.log(LogLevel.WARNING, *messages)
    
    def debug(self, *messages):
        self.log(LogLevel.DEBUG, *messages)
    
    def info(self, *messages):
        self.log(LogLevel.INFO, *messages)
