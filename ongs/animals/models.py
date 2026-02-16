from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
import qrcode
import os


# ==========================================
# PERFIL DO USUÁRIO (Controle de Papéis)
# ==========================================

class Perfil(models.Model):

    TIPOS = (
        ('ADMIN', 'Administrador'),
        ('ONG', 'ONG'),
        ('PROTETOR', 'Protetor'),
        ('COMUM', 'Usuário Comum'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS)

    telefone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.tipo}"


# ==========================================
# ANIMAL
# ==========================================

class Animal(models.Model):

    nome = models.CharField(max_length=100)
    especie = models.CharField(max_length=50)
    raca = models.CharField(max_length=50)

    # Agora ligado diretamente ao User
    responsavel = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="animais"
    )

    foto = models.ImageField(
        upload_to='animais/',
        blank=True,
        null=True
    )

    qr_code = models.ImageField(
        upload_to='qrcodes/',
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if not self.qr_code:

            # URL dinâmica (não fixa IP)
            url = settings.SITE_URL + reverse('animal_public_detail', args=[self.id])

            img = qrcode.make(url)

            qr_path = os.path.join(
                settings.MEDIA_ROOT,
                'qrcodes'
            )

            os.makedirs(qr_path, exist_ok=True)

            caminho_completo = os.path.join(
                qr_path,
                f'animal_{self.id}.png'
            )

            img.save(caminho_completo)

            self.qr_code = f'qrcodes/animal_{self.id}.png'
            super().save(update_fields=['qr_code'])

    def __str__(self):
        return self.nome


# ==========================================
# LOCALIZAÇÃO
# ==========================================

class Localizacao(models.Model):

    animal = models.ForeignKey(
        Animal,
        on_delete=models.CASCADE,
        related_name="localizacoes"
    )

    latitude = models.FloatField()
    longitude = models.FloatField()
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.animal.nome} - {self.data}"
