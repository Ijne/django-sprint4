"""Конфигурация статических страниц."""

from django.apps import AppConfig


class PagesConfig(AppConfig):
    """Настройки приложения страниц."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pages'
