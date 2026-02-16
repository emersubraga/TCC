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
    """
    Captura o select do signup: name="tipo_solicitado"
    e salva como solicitação pendente (ONG/PROTETOR),
    mantendo o tipo final como COMUM até aprovação do ADMIN.
    """
    tipo = (request.POST.get("tipo_solicitado") or "COMUM").upper()

    # Segurança: só permite esses valores
    if tipo not in ["ONG", "PROTETOR", "COMUM"]:
        tipo = "COMUM"

    # O perfil já deve existir pelo post_save, mas garantimos
    perfil, _ = Perfil.objects.get_or_create(user=user, defaults={"tipo": "COMUM"})

    if tipo in ["ONG", "PROTETOR"]:
        # Mantém COMUM e cria solicitação pendente
        perfil.tipo = "COMUM"
        perfil.solicitacao_tipo = tipo
        perfil.solicitacao_status = "PENDENTE"
        perfil.solicitacao_data = timezone.now()
        perfil.save()
    else:
        # Caso COMUM, limpa qualquer solicitação
        perfil.tipo = "COMUM"
        perfil.solicitacao_tipo = None
        perfil.solicitacao_status = "NENHUMA"
        perfil.solicitacao_data = None
        perfil.save()
