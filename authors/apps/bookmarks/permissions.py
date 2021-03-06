from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a bookmark to edit its details.
    """
    message = ("You are not the owner of this bookmark"
               " and cannot access or change it\'s details.")

    def has_object_permission(self, request, view, obj):
        # Permissions are only allowed to the owner of the bookmark.
        return obj.profile == request.user.profile
