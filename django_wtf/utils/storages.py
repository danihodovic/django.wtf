# pylint: disable=abstract-method
from storages.backends.s3boto3 import S3Boto3Storage


class MediaRootS3Boto3Storage(S3Boto3Storage):
    location = "media"
    file_overwrite = False
