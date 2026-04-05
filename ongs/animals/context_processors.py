from .models import Notificacao

def notificacoes_context(request):
    if request.user.is_authenticated:
        count = Notificacao.objects.filter(
            usuario=request.user,
            lida=False
        ).count()
    else:
        count = 0

    return {
        "notificacoes_nao_lidas": count
    }