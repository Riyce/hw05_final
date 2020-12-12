from django import forms
from django.forms.widgets import Textarea

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image",)
        labels = {
            "group": ("Выберете группу"),
            "text": ("Текст"),
            "image": ("Изображение"),
        }
        help_texts = {
            "group": ("Выберете группу из списка доступных."),
            "text": ("Введите текст Вашего поста."),
            "image": ("Добавьте изображение."),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {"text": "Текст комментария"}
        help_texts = {"text": "Введите текст Вашего комментария."}
        widgets = {"text": Textarea()}
