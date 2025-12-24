from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from server_examples.django_rest_framework.users.models import User
from server_examples.django_rest_framework.users.serializers import UserRequestSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()  # type: ignore[assignment]
    serializer_class = UserSerializer

    @extend_schema(operation_id="list_users")
    def list(self, request):
        return super().list(request)

    @extend_schema(operation_id="create_user", request=UserRequestSerializer)
    def create(self, request):
        return super().create(request)

    @extend_schema(operation_id="get_user")
    def retrieve(self, request, pk=None):
        return super().retrieve(request, pk)
