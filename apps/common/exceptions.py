from rest_framework.exceptions import APIException


class Conflict(APIException):
    status_code = 409
    default_detail = "The requested operation conflicts with the current state."
    default_code = "conflict"
