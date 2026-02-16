from multiprocessing import context
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Max, Count
from datetime import timedelta
import json

from .forms import AnimalForm

from .models import Animal, Localizacao, Perfil


# ============================
# HELPERS
# ============================

def get_perfil(user):
    perfil, _ = Perfil.objects.get_or_create(user=user, defaults={"tipo": "COMUM"})
    return perfil


def can_manage_animals(perfil):
    return perfil.tipo in ["ADMIN", "ONG", "PROTETOR"]


# ============================
# DASHBOARD
# ============================

@login_required
def dashboard(request):
    perfil = get_perfil(request.user)

    # Base queryset conforme tipo
    if perfil.tipo == "ADMIN":
        animais_qs = Animal.objects.all()
    elif perfil.tipo in ["ONG", "PROTETOR"]:
        animais_qs = Animal.objects.filter(responsavel=request.user)
    else:
        animais_qs = Animal.objects.all()

    total_animais = animais_qs.count()

    # "ONG" exibida (não existe nome no Perfil, então usa username)
    ong_nome = request.user.username

    # Hoje
    hoje = timezone.localdate()

    # Atualizados Hoje = animais que tiveram alguma localização hoje
    atualizados_hoje = (
        Localizacao.objects
        .filter(animal__in=animais_qs, data__date=hoje)
        .values("animal_id")
        .distinct()
        .count()
    )

    # Sem atualização = animais sem localização nos últimos 7 dias (ou nunca)
    limite = timezone.now() - timedelta(days=7)

    # último update por animal (via Localizacao)
    animais_com_ultima = (
        animais_qs
        .annotate(ultima_localizacao=Max("localizacoes__data"))
    )

    sem_atualizacao = (
        animais_com_ultima
        .filter(ultima_localizacao__lt=limite)  # atualizou faz mais de 7 dias
        .count()
        +
        animais_com_ultima
        .filter(ultima_localizacao__isnull=True)  # nunca atualizou
        .count()
    )

    # Últimos animais atualizados = ordena pela última localização
    ultimos_animais = (
        animais_qs
        .annotate(ultima_localizacao=Max("localizacoes__data"))
        .filter(ultima_localizacao__isnull=False)
        .order_by("-ultima_localizacao")[:10]
    )

    # (mantém o que você já tinha, se quiser exibir em outro lugar)
    total_localizacoes = Localizacao.objects.filter(animal__in=animais_qs).count()

    return render(request, "dashboard.html", {
        "perfil": perfil,
        "animais": animais_qs,
        "total_animais": total_animais,
        "total_localizacoes": total_localizacoes,

        # variáveis que o trecho do template precisa:
        "atualizados_hoje": atualizados_hoje,
        "sem_atualizacao": sem_atualizacao,
        "ong_nome": ong_nome,
        "ultimos_animais": ultimos_animais,
    })


# ============================
# LISTA (logado)
# ============================

@login_required
def animal_list(request):
    perfil = get_perfil(request.user)

    if perfil.tipo == "ADMIN":
        animais = Animal.objects.all()
    elif perfil.tipo in ["ONG", "PROTETOR"]:
        animais = Animal.objects.filter(responsavel=request.user)
    else:
        animais = Animal.objects.all()

    return render(request, "animals/list.html", {
        "animais": animais,
        "perfil": perfil
    })


# ============================
# DETALHE PÚBLICO (QR) — SEM HISTÓRICO
# ============================

def animal_public_detail(request, id):
    animal = get_object_or_404(Animal, id=id)
    perfil_responsavel = get_perfil(animal.responsavel)

    context = {
        "animal": animal,
        "perfil_responsavel": perfil_responsavel
    }

    return render(request, "animals/public_detail.html", context) 



# ============================
# DETALHE PRIVADO — COM HISTÓRICO + MAPA
# ============================

def animal_detail(request, id):
    perfil = get_perfil(request.user)
    animal = get_object_or_404(Animal, id=id)

    if perfil.tipo != "ADMIN" and animal.responsavel != request.user:
        messages.error(request, "Você não tem permissão para ver as localizações deste animal.")
        return redirect("animal_list")

    localizacoes = animal.localizacoes.order_by("-data")
    ultima_localizacao = localizacoes.first()

    perfil_responsavel = get_perfil(animal.responsavel)

    return render(request, "animals/detail.html", {
        "animal": animal,
        "localizacoes": localizacoes,
        "ultima_localizacao": ultima_localizacao,
        "perfil_responsavel": perfil_responsavel,  # <- NOVO
        "modo_publico": False
    })



# ============================
# CREATE
# ============================

@login_required
def animal_create(request):
    perfil = get_perfil(request.user)
    if not can_manage_animals(perfil):
        messages.error(request, "Apenas ONG/Protetor/Admin podem cadastrar animais.")
        return redirect("dashboard")

    if request.method == "POST":
        form = AnimalForm(request.POST, request.FILES)
        if form.is_valid():
            animal = form.save(commit=False)
            animal.responsavel = request.user
            animal.save()
            messages.success(request, "Animal cadastrado com sucesso!")
            return redirect("animal_list")
    else:
        form = AnimalForm()

    return render(request, "animals/forms.html", {
        "form": form,
        "titulo": "Cadastrar animal",
        "botao": "Cadastrar",
    })


@login_required
def animal_update(request, id):
    perfil = get_perfil(request.user)
    animal = get_object_or_404(Animal, id=id)

    if perfil.tipo != "ADMIN" and animal.responsavel != request.user:
        messages.error(request, "Você não tem permissão para editar este animal.")
        return redirect("animal_list")

    if request.method == "POST":
        form = AnimalForm(request.POST, request.FILES, instance=animal)
        if form.is_valid():
            form.save()
            messages.success(request, "Animal atualizado com sucesso!")
            return redirect("animal_detail", id=animal.id)
    else:
        form = AnimalForm(instance=animal)  # <- aqui vem os dados no formulário

    return render(request, "animals/forms.html", {
        "form": form,
        "titulo": "Editar animal",
        "botao": "Salvar alterações",
        "animal": animal,
    })


# ============================
# DELETE (GET confirma / POST exclui)
# ============================

@login_required
def animal_delete(request, id):
    perfil = get_perfil(request.user)
    animal = get_object_or_404(Animal, id=id)

    if perfil.tipo != "ADMIN" and animal.responsavel != request.user:
        messages.error(request, "Você não tem permissão para excluir este animal.")
        return redirect("animal_list")

    if request.method == "POST":
        animal.delete()
        messages.success(request, "Animal excluído com sucesso!")
        return redirect("animal_list")

    return render(request, "animals/confirm_delete.html", {
        "animal": animal
    })


# ============================
# API – SALVAR LOCALIZAÇÃO (QR)
# ============================

@csrf_exempt
def salvar_localizacao(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            animal = Animal.objects.get(id=data["animal_id"])

            Localizacao.objects.create(
                animal=animal,
                latitude=data["latitude"],
                longitude=data["longitude"]
            )

            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"status": "erro", "mensagem": str(e)}, status=400)

    return JsonResponse({"status": "metodo_invalido"}, status=405)


@login_required
def solicitacoes_list(request):
    perfil = get_perfil(request.user)
    if perfil.tipo != "ADMIN":
        messages.error(request, "Acesso negado.")
        return redirect("dashboard")

    pendentes = Perfil.objects.filter(solicitacao_status="PENDENTE").select_related("user").order_by("-solicitacao_data")

    return render(request, "admin/solicitacoes.html", {"pendentes": pendentes})


@login_required
def solicitacao_aprovar(request, perfil_id):
    perfil_admin = get_perfil(request.user)
    if perfil_admin.tipo != "ADMIN":
        messages.error(request, "Acesso negado.")
        return redirect("dashboard")

    p = get_object_or_404(Perfil, id=perfil_id)

    if request.method == "POST" and p.solicitacao_status == "PENDENTE" and p.solicitacao_tipo in ["ONG", "PROTETOR"]:
        p.tipo = p.solicitacao_tipo
        p.solicitacao_status = "APROVADO"
        p.solicitacao_tipo = None
        p.solicitacao_data = None
        p.save()
        messages.success(request, "Solicitação aprovada!")

    return redirect("solicitacoes_list")


@login_required
def solicitacao_rejeitar(request, perfil_id):
    perfil_admin = get_perfil(request.user)
    if perfil_admin.tipo != "ADMIN":
        messages.error(request, "Acesso negado.")
        return redirect("dashboard")

    p = get_object_or_404(Perfil, id=perfil_id)

    if request.method == "POST" and p.solicitacao_status == "PENDENTE":
        p.tipo = "COMUM"
        p.solicitacao_status = "REJEITADO"
        p.solicitacao_tipo = None
        p.solicitacao_data = None
        p.save()
        messages.success(request, "Solicitação rejeitada!")

    return redirect("solicitacoes_list")
