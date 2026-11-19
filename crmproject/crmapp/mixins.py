
import uuid

from rest_framework.response import Response


class StandardResponseMixin:
    """
    Consistent API response format for FlyingLyte CRM.

    Success:
        success, message, data, request_id

    Error:
        success, message, data, error, request_id
    """

    def get_request_id(self, request=None):
        request = request or getattr(self, "request", None)

        if request is not None:
            if not hasattr(request, "_crm_request_id"):
                request._crm_request_id = str(uuid.uuid4())

            return request._crm_request_id

        return str(uuid.uuid4())

    def success_response(
        self,
        data=None,
        message="Request completed successfully.",
        status_code=200,
    ):
        return Response(
            {
                "success": True,
                "message": message,
                "data": data,
                "request_id": self.get_request_id(),
            },
            status=status_code,
        )

    def error_response(
        self,
        code="request_failed",
        message="Request failed.",
        status_code=400,
        fields=None,
    ):
        return Response(
            {
                "success": False,
                "message": message,
                "data": None,
                "error": {
                    "code": code,
                    "fields": fields or {},
                },
                "request_id": self.get_request_id(),
            },
            status=status_code,
        )

    # Compatibility with your existing self.error() calls.
    def error(
        self,
        code,
        message,
        http_status,
        fields=None,
    ):
        return self.error_response(
            code=code,
            message=message,
            status_code=http_status,
            fields=fields,
        )
