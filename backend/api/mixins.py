from django.shortcuts import get_object_or_404
from recipes.models import Recipe
from rest_framework import status
from rest_framework.response import Response
from users.models import User


def create_relation(request, obj_id, model_class, serializer_class, obj_model,
                    user_field='user', obj_field='recipe', error_exists=None,
                    error_self=None, check_self=False):
    """Создаёт отношения между пользователем и объектом."""
    user = request.user
    obj = get_object_or_404(obj_model, id=obj_id)

    if check_self and user == obj:
        return Response(
            {
                'error': error_self or 'Нельзя подписаться на себя'},
            status=status.HTTP_400_BAD_REQUEST
        )

    filter_kwargs = {user_field: user, obj_field: obj}
    if model_class.objects.filter(**filter_kwargs).exists():
        return Response(
            {'error': error_exists or 'Отношение уже существует'},
            status=status.HTTP_400_BAD_REQUEST
        )

    data = {user_field: user.id, obj_field: obj.id}
    serializer = serializer_class(data=data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data, status=status.HTTP_201_CREATED)


def delete_relation(request, obj_id, model_class, user_field='user',
                    obj_field='recipe', error_not_found=None):
    """Удаляет отношения пользователь - объект."""
    user = request.user

    filter_kwargs = {user_field: user, f'{obj_field}_id': obj_id}
    deleted, _ = model_class.objects.filter(**filter_kwargs).delete()

    if not deleted:
        return Response(
            {'error': error_not_found or 'Отношение не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionActionMixin:
    """Миксин для действий с коллекциями рецептов."""

    def handle_collection_action(self, request, pk, model_class,
                                 serializer_class, error_exists,
                                 error_not_found):
        """Обрабатывает действия добавления/удаления рецептов в коллекции."""
        if request.method == 'POST':
            return create_relation(
                request=request,
                obj_id=pk,
                model_class=model_class,
                serializer_class=serializer_class,
                obj_model=Recipe,
                error_exists=error_exists
            )
        elif request.method == 'DELETE':
            return delete_relation(
                request=request,
                obj_id=pk,
                model_class=model_class,
                error_not_found=error_not_found
            )


class SubscriptionActionMixin:
    """Миксин для действий с подписками на авторов."""

    def handle_subscription_action(self, request, user_id, model_class,
                                   serializer_class):
        """Обрабатывает действия подписки/отписки от авторов."""
        if request.method == 'POST':
            return create_relation(
                request=request,
                obj_id=user_id,
                model_class=model_class,
                serializer_class=serializer_class,
                obj_model=User,
                user_field='user',
                obj_field='author',
                error_exists='Вы уже подписаны на этого автора',
                error_self='Нельзя подписаться на самого себя',
                check_self=True
            )
        elif request.method == 'DELETE':
            return delete_relation(
                request=request,
                obj_id=user_id,
                model_class=model_class,
                user_field='user',
                obj_field='author',
                error_not_found='Вы не подписаны на этого автора'
            )
