"""Конфигурация приложения блога."""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Настройки приложения публикаций."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    verbose_name = 'Блог'
