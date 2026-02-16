from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import Perfil


@receiver(post_save, sender=User)
def criar_perfil_automatico(sender, instance, created, **kwargs):
    if created:
        # Por padrão, todo usuário nasce como COMUM.
        Perfil.objects.create(user=instance, tipo='COMUM')

