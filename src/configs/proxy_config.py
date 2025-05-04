from loguru import logger
import os

def set_proxy():
    logger.info("Setting up proxy configuration.")
    proxy_host = "10.0.1.223"
    proxy_port = 7890
    os.environ["http_proxy"] = f"http://{proxy_host}:{proxy_port}"
    os.environ["https_proxy"] = f"http://{proxy_host}:{proxy_port}"