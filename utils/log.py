import logging
import os

from settings import Config

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler(os.path.join(Config.BASE_DIR+"/logs/log.txt"))
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# console = logging.StreamHandler()
# console.setLevel(logging.INFO)
#
# logger.addHandler(handler)
# logger.addHandler(console)
#
# logger.debug("Do something")
# logger.info("Start print log")
# logger.warning("Something maybe fail.")
# logger.error('error')