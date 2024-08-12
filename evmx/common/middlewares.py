import json

import environ
from django.conf import settings
from django.http import HttpRequest
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from common.http_codes import HTTP_400000_INVALID_APPID
from common.http_codes import HTTP_400003_IP_FORBIDDEN
from common.http_codes import HTTP_400004_SIGNATURE_ERROR
from common.http_codes import HTTP_400005_PROJECT_NOT_READY
from common.utils.crypto import validate_hmac
from common.utils.security import is_ip_in_whitelist
from config.settings.unfold.admin import UNFOLD as ADMIN_UNFOLD
from config.settings.unfold.console import UNFOLD as CONSOLE_UNFOLD
from globals.models import Project


class EVMxMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _is_api_request(request: HttpRequest) -> bool:
        return request.path.startswith("/api/")

    @staticmethod
    def get_project(request: HttpRequest) -> Project | None:
        appid = request.headers.get("Appid", None)

        try:
            return Project.retrieve(appid=appid)

        except Project.DoesNotExist:
            return None


class ProjectCheckMiddleware(EVMxMiddleware):
    def __call__(self, request: HttpRequest):
        if self._is_api_request(request):
            project = self.get_project(request)
            if not project:
                return JsonResponse(
                    {
                        "code": HTTP_400000_INVALID_APPID,
                        "msg": _("Appid 错误"),
                    },
                    status=400,
                )

            ready, msg = project.is_ready
            if not ready:
                return JsonResponse(
                    {"code": HTTP_400005_PROJECT_NOT_READY, "msg": msg},
                    status=400,
                )

        return self.get_response(request)


class IPWhiteListMiddleware(EVMxMiddleware):
    def __call__(self, request: HttpRequest):
        if self._is_api_request(request):
            x_forwarded_for = request.headers.get("x-forwarded-for")
            if x_forwarded_for:
                client_ip = x_forwarded_for.split(",")[0]  # real client's ip
            else:
                client_ip = request.META.get("REMOTE_ADDR")

            if not is_ip_in_whitelist(
                whitelist=self.get_project(request).ip_white_list,
                ip=client_ip,
            ):
                return JsonResponse(
                    {"code": HTTP_400003_IP_FORBIDDEN, "msg": _("IP 无权限")},
                    status=403,
                )

        return self.get_response(request)


class HMACMiddleware(EVMxMiddleware):
    def __call__(self, request: HttpRequest):
        if self._is_api_request(request):
            if not self._is_valid_hmac(request):
                return JsonResponse(
                    {"code": HTTP_400004_SIGNATURE_ERROR, "msg": _("签名错误")},
                    status=403,
                )
        return self.get_response(request)

    def _is_valid_hmac(self, request: HttpRequest) -> bool:
        if environ.Env().str("DJANGO_SETTINGS_MODULE") == "config.settings.local":
            return True

        return validate_hmac(
            message_dict=json.loads(request.body),
            key=self.get_project(request).hmac_key,
            signature=request.headers.get("Signature"),
        )


class ConsoleMiddleware(EVMxMiddleware):
    def __call__(self, request: HttpRequest):
        if request.user.is_superuser:
            settings.UNFOLD = ADMIN_UNFOLD
        else:
            if request.user.is_staff:
                CONSOLE_UNFOLD["SIDEBAR"]["navigation"][0]["items"][0]["link"] = (
                    reverse_lazy(
                        "admin:globals_project_change",
                        args=[request.user.project.pk],
                    )
                )

            settings.UNFOLD = CONSOLE_UNFOLD

        return self.get_response(request)
