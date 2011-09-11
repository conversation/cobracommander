import logging

def get_logger(name):
    logging.basicConfig(level=logging.INFO, 
        format='[%(asctime)s] %(name)-45s %(levelname)-12s %(message)s')
    return logging.getLogger(name)