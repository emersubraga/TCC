from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Animal, Localizacao, Perfil


# ==========================================
# ANIMAL ADMIN
# ==========================================

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "nome",
        "especie",
        "raca",
        "responsavel",
        "aprovacao_status",
        "aprovacao_data",
        "mostrar_foto",
        "mostrar_qr",
    )

    list_filter = ("especie", "responsavel", "aprovacao_status", "status")
    search_fields = ("nome", "raca", "responsavel__username")

    readonly_fields = ("qr_code", "preview_qr", "preview_foto", "aprovacao_data", "aprovado_por")

    fieldsets = (
        ("Dados do Animal", {
            "fields": ("nome", "especie", "raca", "status", "sexo", "porte", "vacinado", "castrado", "idade_anos", "idade_meses", "historia", "foto")
        }),
        ("Responsável", {
            "fields": ("responsavel",)
        }),
        ("Aprovação", {
            "fields": ("aprovacao_status", "aprovacao_motivo", "aprovado_por", "aprovacao_data")
        }),
        ("QR Code", {
            "fields": ("preview_qr", "qr_code")
        }),
    )

    actions = ["aprovar_animais", "rejeitar_animais"]

    def aprovar_animais(self, request, queryset):
        # ✅ NÃO usar update() porque precisa chamar save() para gerar QR
        for animal in queryset:
            animal.aprovacao_status = "APROVADO"
            animal.aprovado_por = request.user
            animal.aprovacao_data = timezone.now()
            animal.aprovacao_motivo = ""
            animal.save()  # <-- gera QR aqui, se não tiver
        self.message_user(request, "Animais aprovados com sucesso!")

    aprovar_animais.short_description = "Aprovar animais selecionados"

    def rejeitar_animais(self, request, queryset):
        for animal in queryset:
            animal.aprovacao_status = "REJEITADO"
            animal.aprovado_por = request.user
            animal.aprovacao_data = timezone.now()
            if not animal.aprovacao_motivo:
                animal.aprovacao_motivo = "Rejeitado pelo administrador."
            animal.save()
        self.message_user(request, "Animais rejeitados!")

    rejeitar_animais.short_description = "Rejeitar animais selecionados"

    def preview_qr(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="150" />', obj.qr_code.url)
        return "QR Code ainda não gerado"

    def preview_foto(self, obj):
        if obj.foto:
            return format_html('<img src="{}" width="150" style="border-radius:10px;" />', obj.foto.url)
        return "Sem foto"

    def mostrar_qr(self, obj):
        return "✔️" if obj.qr_code else "❌"

    def mostrar_foto(self, obj):
        return "✔️" if obj.foto else "❌"

    preview_qr.short_description = "QR Code"
    preview_foto.short_description = "Foto"


# ==========================================
# PERFIL ADMIN
# ==========================================

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo', 'telefone')
    list_filter = ('tipo',)
    search_fields = ('user__username',)


# ==========================================
# LOCALIZAÇÃO ADMIN
# ==========================================

@admin.register(Localizacao)
class LocalizacaoAdmin(admin.ModelAdmin):
    list_display = ('animal', 'latitude', 'longitude', 'data')
    list_filter = ('animal',)
