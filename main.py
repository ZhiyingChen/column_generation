import time
import logging
from source.utils.log_setup import setup_log
from source.context import Context

if __name__ == "__main__":
    st = time.time()
    try:
        logger = setup_log(log_dir='output/')
        context = Context()
        context.run()

        logging.info("Total running time: {}".format(time.time() - st))
    except BaseException:
        logging.info("Total running time: {}".format(time.time() - st))
        raise BaseException
