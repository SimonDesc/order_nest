# Bibliothèques standard
import os.path
import re
import time

# Biblioethèque AWS
import boto3

# Imports Django
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


def is_allowed_extension(filename):
    """
    Vérifie si l'extension du fichier est autorisée.
    """
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif"}
    _, ext = os.path.splitext(filename)
    return ext.lower() in allowed_extensions


def clean_filename(filename):
    """
    Nettoie le nom de fichier en remplaçant les caractères spéciaux.
    """
    name, ext = os.path.splitext(filename)
    # Remplacer tous les caractères non alphanumériques (sauf le point de l'extension) par des underscores
    name = re.sub(r"[^\w]", "_", name)
    return f"{name}{ext}"


def unique_file_name(original_name, order_id):
    """
    Génère un nom de fichier unique en utilisant un UUID et un horodatage.
    """
    basename, ext = os.path.splitext(original_name)
    timestamp = time.strftime("%Y%m%d-%H%M%S")

    return f"{basename}_{order_id}_{timestamp}{ext}"
