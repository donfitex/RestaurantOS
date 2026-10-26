from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


def validate_image_upload(value):
    if not value:
        return
    if value.size > getattr(settings, "MAX_IMAGE_UPLOAD_BYTES", 5 * 1024 * 1024):
        raise ValidationError("Image files must be no larger than 5 MB.")
    extension = Path(value.name).suffix.lower()
    formats = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}
    if extension not in formats:
        raise ValidationError("Upload a JPEG, PNG, or WebP image.")
    try:
        value.seek(0)
        with Image.open(value) as image:
            if image.format != formats[extension]:
                raise ValidationError("Image content does not match its file extension.")
            if image.width * image.height > getattr(settings, "MAX_IMAGE_PIXELS", 20_000_000):
                raise ValidationError("Image dimensions are too large.")
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError):
        raise ValidationError("Upload a valid image.") from None
    finally:
        value.seek(0)
