from django.db import models
from django.conf import settings
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("animals/", views.animal_list, name="animal_list"),
    path("animals/novo/", views.animal_create, name="animal_create"),
    path("animals/<int:id>/", views.animal_detail, name="animal_detail"),            # privado
    path("animals/<int:id>/editar/", views.animal_update, name="animal_update"),
    path("animals/<int:id>/excluir/", views.animal_delete, name="animal_delete"),

    path("animais/", views.animais_publicos, name="animais_publicos"),
    path("animal/<int:id>/", views.animal_public_detail, name="animal_public_detail"),  # público (QR)
    
    path("api/localizacao/", views.salvar_localizacao, name="salvar_localizacao"),
    path("solicitacoes/", views.solicitacoes_list, name="solicitacoes_list"),
    path("solicitacoes/<int:perfil_id>/aprovar/", views.solicitacao_aprovar, name="solicitacao_aprovar"),
    path("solicitacoes/<int:perfil_id>/rejeitar/", views.solicitacao_rejeitar, name="solicitacao_rejeitar"),
    path("conta/", views.account_settings, name="account_settings"),

    path("adocao/interesse/<int:animal_id>/", views.interesse_adocao, name="interesse_adocao"),
    path("api/encontrei/", views.api_encontrei, name="api_encontrei"),

    path("animais/pendentes/", views.animais_pendentes, name="animais_pendentes"),
    path("animais/<int:id>/aprovar/", views.animal_aprovar, name="animal_aprovar"),
    path("animais/<int:id>/rejeitar/", views.animal_rejeitar, name="animal_rejeitar"),
    
]


