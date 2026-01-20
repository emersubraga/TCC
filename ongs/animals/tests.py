from django.test import TestCase
from django.urls import reverse
from .models import Animal, Protetor, Localizacao
import json

class AnimalTestCase(TestCase):

    def setUp(self):
        self.protetor = Protetor.objects.create(
            nome="ONG Protetores",
            telefone="(88) 99999-9999",
            email="contato@ong.com"
        )

        self.animal = Animal.objects.create(
            nome="Rex",
            especie="Cachorro",
            raca="Vira-lata",
            protetor=self.protetor
        )

    def test_criacao_animal(self):
        """Testa se o animal foi criado corretamente"""
        self.assertEqual(self.animal.nome, "Rex")
        self.assertEqual(self.animal.especie, "Cachorro")

    def test_acesso_pagina_animal(self):
        """Testa se a página do animal responde corretamente"""
        url = reverse('animal_detail', args=[self.animal.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rex")

    def test_salvar_localizacao(self):
        """Testa se a localização é salva via API"""
        url = reverse('salvar_localizacao')

        data = {
            "animal_id": self.animal.id,
            "latitude": -3.71722,
            "longitude": -38.5434
        }

        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Localizacao.objects.count(), 1)