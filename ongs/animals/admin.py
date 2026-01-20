from django.contrib import admin
from .models import Animal, Protetor, Localizacao
from .utils import gerar_qr_code
from django.utils.html import format_html


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'especie', 'raca', 'protetor', 'mostrar_foto', 'mostrar_qr')
    readonly_fields = ('qr_code', 'preview_qr', 'preview_foto')

    fieldsets = (
        ('Dados do Animal', {
            'fields': ('nome', 'especie', 'raca', 'foto')
        }),
        ('Responsável', {
            'fields': ('protetor',)
        }),
        ('QR Code', {
            'fields': ('preview_qr', 'qr_code')
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not obj.qr_code:
            gerar_qr_code(obj)

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


admin.site.register(Protetor)
admin.site.register(Localizacao)
