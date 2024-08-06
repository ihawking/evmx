from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class RejectAll(BasePermission):
    def has_permission(self, request: Request, view):
        return False

    def has_object_permission(self, request, view, obj):
        return False
