import logging
import logging.config
from pathlib import Path

config_path = Path(__file__).parent / "logging.conf"
# log_file_path = path.join(path.dirname(path.abspath(__file__)), 'log.config')
# print(config_path)
logging.config.fileConfig(config_path)
logger = logging.getLogger('ragPdmClassifier')  