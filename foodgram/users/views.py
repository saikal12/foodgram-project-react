from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser import serializers
from djoser.views import UserViewSet
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from api1.pagination import CustomPagination
from recipes.models import Follow
from api1.serializer import FollowSerializer, MyUserCreateSerializer, MyUserSerializer, FollowCreateSerializer

# Create your views here.


User = get_user_model()


class MyUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = MyUserSerializer
    pagination_class = CustomPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(AllowAny,)
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(follow__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(AllowAny,)
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            data = {
                'user': user.id,
                'author': id
            }
            subscribe = FollowCreateSerializer(data=data)
            subscribe.is_valid(raise_exception=True)
            subscribe.save()
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            obj = get_object_or_404(Follow, user=user, author=author)
            if not obj:
                raise serializers.ValidationError(
                    {
                        'errors': [
                            'Вы не подписаны на этого автора.'
                        ]
                    }
                )
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
