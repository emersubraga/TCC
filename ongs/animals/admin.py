from django.contrib import admin
from django.utils.html import format_html
from .models import Animal, Localizacao, Perfil


# ==========================================
# ANIMAL ADMIN
# ==========================================

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'especie',
        'raca',
        'responsavel',
        'mostrar_foto',
        'mostrar_qr'
    )

    list_filter = ('especie', 'responsavel')
    search_fields = ('nome', 'raca')

    readonly_fields = ('qr_code', 'preview_qr', 'preview_foto')

    fieldsets = (
        ('Dados do Animal', {
            'fields': ('nome', 'especie', 'raca', 'foto')
        }),
        ('Responsável', {
            'fields': ('responsavel',)
        }),
        ('QR Code', {
            'fields': ('preview_qr', 'qr_code')
        }),
    )

    def preview_qr(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="150" />',
                obj.qr_code.url
            )
        return "QR Code ainda não gerado"

    def preview_foto(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" width="150" style="border-radius:10px;" />',
                obj.foto.url
            )
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
