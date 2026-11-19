from rest_framework_simplejwt.views import TokenRefreshView
from .mixins import StandardResponseMixin


class CRMTokenRefreshView(StandardResponseMixin, TokenRefreshView):

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code != 200:
            return response

        return self.success_response(
            data=response.data,
            message="Token refreshed successfully.",
            status_code=200,
        )