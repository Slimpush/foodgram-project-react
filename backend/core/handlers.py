import os

from django.db.models.signals import post_delete
from django.dispatch import receiver
from recipes.models import Recipe


@receiver(post_delete, sender=Recipe)
def delete_image(sender: Recipe, instance: Recipe, **kwargs) -> None:
    image_path = instance.image.path
    if os.path.exists(image_path):
        os.remove(image_path)
