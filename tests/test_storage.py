from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from apps.common.validators import validate_image_upload


def image_file(name="dish.png", size=(8, 8)):
    buffer = BytesIO()
    Image.new("RGB", size, "green").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def test_valid_image_is_accepted_and_rewound():
    upload = image_file()
    validate_image_upload(upload)
    assert upload.tell() == 0


@pytest.mark.parametrize(
    "name,content",
    [("dish.svg", b"<svg/>"), ("dish.png", b"<html>bad</html>"), ("dish.exe", b"MZ")],
)
def test_invalid_upload_rejected(name, content):
    with pytest.raises(ValidationError):
        validate_image_upload(SimpleUploadedFile(name, content))


def test_extension_must_match_content():
    with pytest.raises(ValidationError):
        validate_image_upload(image_file("dish.jpg"))


@override_settings(MAX_IMAGE_PIXELS=100)
def test_excessive_pixel_dimensions_rejected():
    with pytest.raises(ValidationError):
        validate_image_upload(image_file(size=(11, 10)))


@override_settings(MAX_IMAGE_UPLOAD_BYTES=1)
def test_upload_size_limit_enforced():
    with pytest.raises(ValidationError):
        validate_image_upload(image_file())
