import logging, os, time, datetime

def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_test_logger(log_path, TAG):
    ''' Get the standard test class logger '''
    create_dir(log_path)
    log = logging.getLogger(None)
    if log.handlers:
        # If logger is already attached with handlers, return it.
        return log
    log.setLevel(logging.DEBUG)
    c_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    # Log info to stream
    ch = logging.StreamHandler()
    ch.setFormatter(c_formatter)
    ch.setLevel(logging.INFO)
    # Log everything to file
    f_formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh = logging.FileHandler(log_path + TAG + "_"
                             + time.strftime("%m-%d-%Y_%H-%M-%S") + '.log')
    fh.setFormatter(f_formatter)
    fh.setLevel(logging.DEBUG)
    log.addHandler(ch)
    log.addHandler(fh)
    return log

def get_test_reporter(log_path, TAG):
    ''' Get the standard report logger '''
    create_dir(log_path)
    f = open(log_path + TAG + "_" + time.strftime("%m-%d-%Y_%H-%M-%S")
             + '.report', 'w')
    return f