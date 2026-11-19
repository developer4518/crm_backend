"""Standardize DRF-generated errors for the FlyingLyte CRM API."""
from uuid import uuid4

from rest_framework.views import exception_handler


def crm_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        # Unhandled exceptions should still be logged and processed as 500s.
        return None

    request = context.get("request")
    if request is not None:
        request_id = getattr(request, "_crm_request_id", None)
        if not request_id:
            request_id = str(uuid4())
            request._crm_request_id = request_id
    else:
        request_id = str(uuid4())

    original = response.data
    code = getattr(exc, "default_code", "request_failed")
    if hasattr(exc, "get_codes"):
        codes = exc.get_codes()
        if isinstance(codes, str):
            code = codes

    detail = original.get("detail") if isinstance(original, dict) else None
    message = str(detail) if detail is not None else "Request validation failed."
    fields = (
        {k: v for k, v in original.items() if k != "detail"}
        if isinstance(original, dict)
        else {}
    )
    response.data = {
        "success": False,
        "message": message,
        "data": None,
        "error": {"code": str(code), "fields": fields},
        "request_id": request_id,
    }
    response["Cache-Control"] = "no-store"
    return response
