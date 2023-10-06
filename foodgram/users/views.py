from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser import serializers
from djoser.views import UserViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from recipes.models import Follow
from api1.serializer import FollowSerializer, MyUserCreateSerializer, MyUserSerializer

# Create your views here.


User = get_user_model()


class MyUserViewSet(UserViewSet):
    serializer_class = MyUserCreateSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=('IsAuthenticated',),
        serializer_class=MyUserSerializer
    )
    def subscription(self, request):
        user = request.user

        def queryset():
            return User.objects.filter(follow__user=user)

        self.get_queryset = queryset
        return self.list(queryset)

    @action(
        detail=False,
        methods=['post', 'delete'],
        permission_classes=('IsAuthenticated',),
        serializer_class=MyUserSerializer

    )
    def subscribe(self, request, id):
        user = request.user
        author = self.get_object()
        if request.methods == 'POST':
            data = {
                'user': user.id,
                'author': id
            }
            subscribe = FollowSerializer(data=data)
            subscribe.is_valid(raise_exception=True)
            subscribe.save()
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.methods == 'DELETE':
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
