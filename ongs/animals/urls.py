from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('animal/<int:id>/', views.animal_detail, name='animal_detail'),
    path('api/localizacao/', views.salvar_localizacao, name='salvar_localizacao'),
]

