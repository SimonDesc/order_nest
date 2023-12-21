import boto3
from django.conf import settings


def delete_file_from_s3(object_key):
    """
    Supprime un fichier du bucket S3.
    """
    s3_client = boto3.client('s3',
                             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                             region_name=settings.AWS_S3_REGION_NAME)
    try:
        s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=object_key)
    except Exception as e:
        print("Erreur lors de la suppression du fichier : ", e)
        return False
    return True
