import time
import logging
logging.basicConfig(level=logging.INFO)


def main():

    while True:
        logging.info('Woke up')
        time.sleep(1)


if __name__ == '__main__':
    main()
