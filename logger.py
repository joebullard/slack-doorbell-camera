import time

def log(level, message):
    """Helper logging function. Could be extended later

    Args:
        level: LogLevel enum selection
        message: message which becomes arg of the LogLevel enum function
    Returns:
        None
    """
    time_stamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print('%s: (%s) %s' % (level, time_stamp, message))

def fatal(message):
    log('FATAL', message)

def error(message):
    log('ERROR', message)

def warn(message):
    log('WARNING', message)

def info(message):
    log('INFO', message)
