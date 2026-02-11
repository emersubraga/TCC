from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Animal, Localizacao

from django.contrib.auth.decorators import login_required

def dashboard(request):
    return render(request, 'dashboard.html')


@csrf_exempt
def salvar_localizacao(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        Localizacao.objects.create(
            animal_id=data['animal_id'],
            latitude=data['latitude'],
            longitude=data['longitude']
        )

        return JsonResponse({'status': 'ok'})


def animal_detail(request, id):
    animal = get_object_or_404(Animal, id=id)

    localizacoes = None
    ultima_localizacao = None

    # 🔐 Só protetor (usuário logado) vê localização
    if request.user.is_authenticated:
        localizacoes = Localizacao.objects.filter(
            animal=animal
        ).order_by('-data')

        ultima_localizacao = localizacoes.first()

    return render(request, 'animal_detail.html', {
        'animal': animal,
        'localizacoes': localizacoes,
        'ultima_localizacao': ultima_localizacao
    })
