# list files of a google cloud storaimport src.configs.config
from src.configs.config import yaml_configs
from loguru import logger

from google.cloud import storage




storage_client = storage.Client()
bucket_name = "jason-hsbc-test"  # Replace with your bucket name
bucket = storage_client.bucket(bucket_name)
blobs = bucket.list_blobs()

for blob in blobs:
    print(blob.name)

logger.info("done")