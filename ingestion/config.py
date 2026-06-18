import logging


SUPPORT_EXT = [".flac"]
GAIN = 10 ** (-3 / 20)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CONVERTION_LOCATION = "./datasets/converted/"
