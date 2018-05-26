from multiprocessing import Pool
import logging


def multi_process(func, data, workers):
    logging.warning('Consuming list with %s workers' % workers)
    p = Pool(workers)
    try:
        # the timeout(.get(9999999) is a workaround for the KeyboardInterrupt. without that it just does not work.
        # Seem to be a bug on multiprocessing. Will investigate it later
        p.map_async(func, data).get(9999999)
        p.close()
    except (KeyboardInterrupt, SystemExit):
        print("Caught KeyboardInterrupt, terminating workers")
    except Exception as e:
        print(e)

