from django.db import models
import qrcode
import os
from django.conf import settings

class Protetor(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return self.nome

class Animal(models.Model):
    nome = models.CharField(max_length=100)
    especie = models.CharField(max_length=50)
    raca = models.CharField(max_length=50)
    protetor = models.ForeignKey(Protetor, on_delete=models.CASCADE)

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
            url = f"http://192.168.3.113:8000/animal/{self.id}/"

            img = qrcode.make(url)

            caminho = os.path.join(
                settings.MEDIA_ROOT,
                'qrcodes',
                f'animal_{self.id}.png'
            )

            img.save(caminho)

            self.qr_code = f'qrcodes/animal_{self.id}.png'
            super().save(update_fields=['qr_code'])

    def __str__(self):
        return self.nome


class Localizacao(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.animal.nome} - {self.data}"

