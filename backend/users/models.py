from core.constants import EMAIL_LENGTH, MAX_FIO_LENGTH, USERNAME_LENGTH
from core.validators import username_validator
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    """Менеджер пользователей с дополнительной функциональностью."""

    def create_user(self, email, username=None, password=None, **extra_fields):
        """
        Создает и сохраняет пользователя с указанным email и паролем.
        """
        if not email:
            raise ValueError('Email обязателен')

        if not username:
            username = self.normalize_email(email).split('@')[0]

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )

        if password:
            user.set_password(password)

        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None,
                         **extra_fields):
        """
        Создает и сохраняет суперпользователя с указанным email и паролем.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """Модель пользователя с дополнительными полями."""

    email = models.EmailField('Почта', unique=True, max_length=EMAIL_LENGTH)
    username = models.CharField(
        'Никнейм',
        unique=True,
        validators=(username_validator,),
        max_length=USERNAME_LENGTH
    )
    first_name = models.CharField('Имя', max_length=MAX_FIO_LENGTH)
    last_name = models.CharField('Фамилия', max_length=MAX_FIO_LENGTH)
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/avatars/',
        blank=True,
        null=True
    )

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    objects = CustomUserManager()

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель для хранения подписок пользователей на авторов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription'
            )
        ]
