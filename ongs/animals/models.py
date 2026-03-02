from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
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

    STATUS_SOLIC = (
        ("NENHUMA", "Nenhuma"),
        ("PENDENTE", "Pendente"),
        ("APROVADO", "Aprovado"),
        ("REJEITADO", "Rejeitado"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS, default="COMUM")
    telefone = models.CharField(max_length=20, blank=True, null=True)

    solicitacao_tipo = models.CharField(max_length=20, choices=TIPOS, blank=True, null=True)
    solicitacao_status = models.CharField(max_length=20, choices=STATUS_SOLIC, default="NENHUMA")
    solicitacao_data = models.DateTimeField(blank=True, null=True)

    ong_cnpj = models.CharField(max_length=18, blank=True, null=True)  # 00.000.000/0000-00
    ong_representante_legal = models.CharField(max_length=120, blank=True, null=True)


    def __str__(self):
        return f"{self.user.username} - {self.tipo}"

# ==========================================
# ANIMAL
# ==========================================

class Animal(models.Model):

    STATUS = (
        ("ADOCAO", "Para adoção"),
        ("ADOTADO", "Adotado"),
        ("PERDIDO", "Perdido"),
        ("TRATAMENTO", "Em tratamento"),
    )

    SEXO = (
        ("M", "Macho"),
        ("F", "Fêmea"),
        ("N", "Não informado"),
    )

    PORTE = (
        ("P", "Pequeno"),
        ("M", "Médio"),
        ("G", "Grande"),
        ("N", "Não informado"),
    )

    nome = models.CharField(max_length=100)
    especie = models.CharField(max_length=50)
    raca = models.CharField(max_length=50)

    # ✅ NOVOS CAMPOS
    status = models.CharField(max_length=20, choices=STATUS, default="ADOCAO")
    sexo = models.CharField(max_length=1, choices=SEXO, default="N")
    porte = models.CharField(max_length=1, choices=PORTE, default="N")

    vacinado = models.BooleanField(default=False)
    castrado = models.BooleanField(default=False)

    # idade aproximada
    idade_anos = models.PositiveSmallIntegerField(blank=True, null=True)
    idade_meses = models.PositiveSmallIntegerField(blank=True, null=True)

    historia = models.TextField(blank=True, null=True)

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

        # ✅ só gera QR quando aprovado
        if self.aprovacao_status == "APROVADO" and not self.qr_code:
            url = settings.SITE_URL + reverse('animal_public_detail', args=[self.id])
            img = qrcode.make(url)

            qr_path = os.path.join(settings.MEDIA_ROOT, 'qrcodes')
            os.makedirs(qr_path, exist_ok=True)

            caminho_completo = os.path.join(qr_path, f'animal_{self.id}.png')
            img.save(caminho_completo)

            self.qr_code = f'qrcodes/animal_{self.id}.png'
            super().save(update_fields=['qr_code'])

    def __str__(self):
        return self.nome
    
    APROVACAO_CHOICES = (
        ("APROVADO", "Aprovado"),
        ("PENDENTE", "Pendente"),
        ("REJEITADO", "Rejeitado"),
    )

    aprovacao_status = models.CharField(
        max_length=10,
        choices=APROVACAO_CHOICES,
        default="APROVADO",
        db_index=True,
    )
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="animais_aprovados",
    )
    aprovacao_data = models.DateTimeField(null=True, blank=True)
    aprovacao_motivo = models.CharField(max_length=255, blank=True, default="")


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


class InteresseAdocao(models.Model):
    STATUS = (
        ("PENDENTE", "Pendente"),
        ("CONTATADO", "Contatado"),
        ("FECHADO", "Fechado"),
    )

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="interesses")
    interessado = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interesses_adocao")

    contato = models.CharField(max_length=120)  # whatsapp/email/telefone
    mensagem = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS, default="PENDENTE")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interesse: {self.animal.nome} - {self.interessado.username}"


class RelatoEncontro(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="relatos_encontro")

    # pode ser anônimo (mas você pode exigir conta se quiser)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="relatos_encontro")

    contato = models.CharField(max_length=120)
    mensagem = models.TextField(blank=True, null=True)

    latitude = models.FloatField()
    longitude = models.FloatField()
    criado_em = models.DateTimeField(auto_now_add=True)

    resolvido = models.BooleanField(default=False)

    def __str__(self):
        return f"Encontro: {self.animal.nome} - {self.criado_em}"