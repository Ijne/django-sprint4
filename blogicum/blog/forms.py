"""Формы приложения блога."""

from django.contrib.auth import get_user_model
from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    """Форма создания и изменения публикации."""

    class Meta:
        """Поля формы публикации."""

        model = Post
        fields = ('title', 'text', 'pub_date', 'location', 'category', 'image')


class CommentForm(ModelForm):
    """Форма комментария."""

    class Meta:
        """Поля формы комментария."""

        model = Comment
        fields = ('text',)


class ProfileForm(ModelForm):
    """Форма редактирования профиля."""

    class Meta:
        """Редактируемые поля пользователя."""

        model = get_user_model()
        fields = ('first_name', 'last_name', 'username', 'email')
