from multiprocessing import context
from urllib import request
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.db.models import Max, Count
from datetime import timedelta
import json
import math

from .forms import AnimalForm, SolicitarTipoForm, UserSettingsForm, PerfilSettingsForm

from .models import Animal, Localizacao, Perfil, InteresseAdocao, RelatoEncontro


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
        animais = Animal.objects.all().order_by("-id")
    elif perfil.tipo in ["ONG", "PROTETOR"]:
        # ✅ dono vê todos os dele (APROVADO/PENDENTE/REJEITADO)
        animais = Animal.objects.filter(responsavel=request.user).order_by("-id")
    else:
        # ✅ usuário comum não deveria gerenciar animais, mas se entrar aqui:
        animais = Animal.objects.filter(responsavel=request.user).order_by("-id")

    return render(request, "animals/list.html", {
        "animais": animais,
        "perfil": perfil
    })


# ============================
# DETALHE PÚBLICO (QR) — SEM HISTÓRICO
# ============================

def animal_public_detail(request, id):
    animal = get_object_or_404(Animal, id=id, aprovacao_status="APROVADO")
    perfil_responsavel = get_perfil(animal.responsavel)

    return render(request, "animals/public_detail.html", {
        "animal": animal,
        "perfil_responsavel": perfil_responsavel
    })



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

    # ✅ novos dados para o responsável
    interesses = animal.interesses.order_by("-criado_em")          # ADOCAO
    relatos = animal.relatos_encontro.order_by("-criado_em")       # PERDIDO

    return render(request, "animals/detail.html", {
        "animal": animal,
        "localizacoes": localizacoes,
        "ultima_localizacao": ultima_localizacao,
        "perfil_responsavel": perfil_responsavel,
        "interesses": interesses,
        "relatos": relatos,
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

    MAX_ANIMAIS_SEM_APROVACAO = 4

    if request.method == "POST":
        form = AnimalForm(request.POST, request.FILES)
        if form.is_valid():
            # ✅ conta apenas APROVADOS (pendentes não “consomem” o limite)
            total_aprovados = Animal.objects.filter(
                responsavel=request.user,
                aprovacao_status="APROVADO"
            ).count()

            animal = form.save(commit=False)
            animal.responsavel = request.user

            if perfil.tipo != "ADMIN" and total_aprovados >= MAX_ANIMAIS_SEM_APROVACAO:
                animal.aprovacao_status = "PENDENTE"
                animal.aprovacao_data = timezone.now()
                animal.aprovacao_motivo = "Limite de 4 animais atingido. Necessita aprovação do administrador."
                animal.save()
                messages.warning(request, "Cadastro enviado para aprovação do administrador (limite de 4 animais atingido).")
                return redirect("animal_list")

            # ✅ até 4 (ou admin): aprovado automaticamente
            animal.aprovacao_status = "APROVADO"
            animal.aprovacao_data = timezone.now()
            animal.aprovacao_motivo = ""
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
    

@login_required
def animais_pendentes(request):
    perfil = get_perfil(request.user)
    if perfil.tipo != "ADMIN":
        messages.error(request, "Apenas administradores podem acessar esta página.")
        return redirect("dashboard")

    pendentes = Animal.objects.filter(aprovacao_status="PENDENTE").order_by("-id")
    return render(request, "animals/pendentes.html", {
        "perfil": perfil,
        "pendentes": pendentes,
        "total_pendentes": pendentes.count(),
    })


@login_required
def animal_aprovar(request, id):
    perfil = get_perfil(request.user)
    if perfil.tipo != "ADMIN":
        messages.error(request, "Apenas administradores podem aprovar animais.")
        return redirect("dashboard")

    animal = get_object_or_404(Animal, id=id)

    if request.method == "POST":
        animal.aprovacao_status = "APROVADO"
        animal.aprovado_por = request.user
        animal.aprovacao_data = timezone.now()
        animal.aprovacao_motivo = ""
        animal.save()  # ✅ chama save() (e gera QR, se você aplicou aquela regra)
        messages.success(request, f"Animal '{animal.nome}' aprovado com sucesso!")
        return redirect("animais_pendentes")

    return redirect("animais_pendentes")


@login_required
def animal_rejeitar(request, id):
    perfil = get_perfil(request.user)
    if perfil.tipo != "ADMIN":
        messages.error(request, "Apenas administradores podem rejeitar animais.")
        return redirect("dashboard")

    animal = get_object_or_404(Animal, id=id)

    if request.method == "POST":
        motivo = (request.POST.get("motivo") or "").strip()
        animal.aprovacao_status = "REJEITADO"
        animal.aprovado_por = request.user
        animal.aprovacao_data = timezone.now()
        animal.aprovacao_motivo = motivo or "Rejeitado pelo administrador."
        animal.save()
        messages.success(request, f"Animal '{animal.nome}' rejeitado.")
        return redirect("animais_pendentes")

    return redirect("animais_pendentes")

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

    if request.method == "POST" and p.solicitacao_status == "PENDENTE":
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


@login_required
def account_settings(request):
    perfil = get_perfil(request.user)

    # forms já existentes (email/telefone etc)
    user_form = UserSettingsForm(instance=request.user)
    perfil_form = PerfilSettingsForm(instance=perfil)

    # form da solicitação
    solicit_form = SolicitarTipoForm(instance=perfil)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "salvar_dados":
            user_form = UserSettingsForm(request.POST, instance=request.user)
            perfil_form = PerfilSettingsForm(request.POST, instance=perfil)

            if user_form.is_valid() and perfil_form.is_valid():
                user_form.save()
                perfil_form.save()
                messages.success(request, "Dados atualizados com sucesso!")
                return redirect("account_settings")
            messages.error(request, "Corrija os campos destacados.")

        elif action == "solicitar_tipo":
            # ✅ SEMPRE por aprovação: bloqueia se já tiver pendente
            if perfil.solicitacao_status == "PENDENTE":
                messages.warning(request, "Você já tem uma solicitação pendente.")
                return redirect("account_settings")

            solicit_form = SolicitarTipoForm(request.POST, instance=perfil)
            if solicit_form.is_valid():
                p = solicit_form.save(commit=False)
                p.solicitacao_status = "PENDENTE"
                p.solicitacao_data = timezone.now()
                # ⚠️ não muda p.tipo aqui
                p.save()
                messages.success(request, "Solicitação enviada para aprovação do administrador.")
                return redirect("account_settings")
            messages.error(request, "Revise os dados da solicitação.")

    return render(request, "account/settings.html", {
        "perfil": perfil,
        "user_form": user_form,
        "perfil_form": perfil_form,
        "solicit_form": solicit_form,
    })


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2) + \
        math.cos(phi1) * math.cos(phi2) * \
        (math.sin(dlambda / 2) ** 2)

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def animais_publicos(request):
    status = request.GET.get("status")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")

    # ✅ novo: raio em km (padrão 2, limite 0.5..50 pra evitar abuso)
    try:
        raio_km = float(request.GET.get("km") or 2)
    except ValueError:
        raio_km = 2

    if raio_km < 0.5:
        raio_km = 0.5
    if raio_km > 50:
        raio_km = 50

    animais = Animal.objects.filter(aprovacao_status="APROVADO")
    aviso = None

    if status:
        animais = animais.filter(status=status)

    if status == "PERDIDO":
        if not lat or not lng:
            aviso = "Permita sua localização e defina um raio (km) para ver animais perdidos próximos."
            animais = Animal.objects.none()
        else:
            try:
                lat = float(lat)
                lng = float(lng)
            except ValueError:
                animais = Animal.objects.none()
                aviso = "Localização inválida."
            else:
                proximos_ids = []
                for animal in animais:
                    ultima = animal.localizacoes.order_by("-data").first()
                    if not ultima:
                        continue

                    distancia = haversine_km(lat, lng, ultima.latitude, ultima.longitude)

                    # ✅ agora usa raio_km
                    if distancia <= raio_km:
                        proximos_ids.append(animal.id)

                animais = Animal.objects.filter(id__in=proximos_ids)

    return render(request, "animals/public_list.html", {
        "animais": animais,
        "status": status,
        "aviso": aviso,
        "raio_km": raio_km,  # ✅ manda para o template
    })


@login_required
def interesse_adocao(request, animal_id):
    animal = get_object_or_404(Animal, id=animal_id)

    # só faz sentido para ADOCAO
    if animal.status != "ADOCAO":
        messages.error(request, "Este animal não está disponível para adoção.")
        return redirect("animal_public_detail", animal_id)

    perfil = get_perfil(request.user)
    contato_padrao = (perfil.telefone or request.user.email or "").strip()

    # ✅ mantém o "next" (pra voltar depois do login e depois do envio)
    next_url = request.GET.get("next", "")
    if next_url and not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next_url = ""

    if request.method == "POST":
        contato = (request.POST.get("contato") or "").strip()
        mensagem = (request.POST.get("mensagem") or "").strip()

        if not contato:
            messages.error(request, "Informe um contato (WhatsApp/telefone/e-mail).")
            return render(request, "animals/interesse_adocao.html", {
                "animal": animal,
                "contato_padrao": contato_padrao,
                "next": next_url,
            })

        InteresseAdocao.objects.create(
            animal=animal,
            interessado=request.user,
            contato=contato,
            mensagem=mensagem or None
        )
        messages.success(request, "Interesse enviado! O responsável pelo animal irá entrar em contato.")

        # ✅ se tiver next, volta pra página que o usuário estava (ex: listagem)
        if next_url:
            return redirect(next_url)

        return redirect("animal_public_detail", animal_id)

    return render(request, "animals/interesse_adocao.html", {
        "animal": animal,
        "contato_padrao": contato_padrao,
        "next": next_url,
    })



@require_POST
def api_encontrei(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido."}, status=400)

    animal_id = data.get("animal_id")
    contato = (data.get("contato") or "").strip()
    mensagem = (data.get("mensagem") or "").strip()
    lat = data.get("latitude")
    lng = data.get("longitude")

    if not animal_id or lat is None or lng is None:
        return JsonResponse({"ok": False, "error": "Dados incompletos."}, status=400)

    if not contato:
        return JsonResponse({"ok": False, "error": "Contato é obrigatório."}, status=400)

    animal = get_object_or_404(Animal, id=animal_id)

    # registra a localização (mesmo modelo já usado pelo sistema)
    Localizacao.objects.create(animal=animal, latitude=float(lat), longitude=float(lng))

    # salva o relato (com usuário se estiver logado)
    usuario = request.user if request.user.is_authenticated else None
    RelatoEncontro.objects.create(
        animal=animal,
        usuario=usuario,
        contato=contato,
        mensagem=mensagem or None,
        latitude=float(lat),
        longitude=float(lng),
    )

    return JsonResponse({"ok": True})