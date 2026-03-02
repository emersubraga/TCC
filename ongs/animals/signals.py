from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.signals import user_signed_up

from .models import Perfil


@receiver(post_save, sender=User)
def criar_perfil_automatico(sender, instance, created, **kwargs):
    if created:
        # Por padrão, todo usuário nasce como COMUM.
        Perfil.objects.create(user=instance, tipo="COMUM")


@receiver(user_signed_up)
def salvar_solicitacao_tipo(sender, request, user, **kwargs):
    tipo = (request.POST.get("tipo_solicitado") or "COMUM").upper()
    if tipo not in ["ONG", "PROTETOR", "COMUM"]:
        tipo = "COMUM"

    perfil, _ = Perfil.objects.get_or_create(user=user, defaults={"tipo": "COMUM"})

    if tipo in ["ONG", "PROTETOR"]:
        perfil.tipo = "COMUM"
        perfil.solicitacao_tipo = tipo
        perfil.solicitacao_status = "PENDENTE"
        perfil.solicitacao_data = timezone.now()

        # se ONG, guarda dados
        if tipo == "ONG":
            perfil.ong_cnpj = (request.POST.get("ong_cnpj") or "").strip()
            perfil.ong_representante_legal = (request.POST.get("ong_representante_legal") or "").strip()

        perfil.save()
