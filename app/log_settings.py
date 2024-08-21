from loguru import logger

logger.add("file.log", rotation="1 MB")
logger.add("info.log", format="<green>{time} {level} {message}</green>", level="INFO")
logger.add("info.log", format="{time} {level} {message}", level="WARNING")
logger.add("error.log", format="{time} {level} {message}", level="ERROR")
logger.add("debug.log", format="{time} {level} {message}", level="DEBUG")
logger.add("info.log", format="{time} {level} {message}", level="CRITICAL")
