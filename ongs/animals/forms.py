from django import forms
from .models import Animal
from django.contrib.auth.models import User
from .models import Perfil


class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = [
            "nome", "especie", "raca",
            "status", "sexo", "porte",
            "idade_anos", "idade_meses",
            "vacinado", "castrado",
            "historia",
            "foto",
        ]
        widgets = {
            "historia": forms.Textarea(attrs={"rows": 4}),
            "idade_anos": forms.NumberInput(attrs={"min": 0}),
            "idade_meses": forms.NumberInput(attrs={"min": 0, "max": 11}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        base = "w-full rounded-xl border border-gray-300 bg-gray-50 px-3 py-2.5 focus:outline-none focus:ring-4 focus:ring-emerald-200 focus:border-emerald-600 transition"
        self.fields["nome"].widget.attrs.update({"class": base, "placeholder": "Ex: Bob"})
        self.fields["especie"].widget.attrs.update({"class": base, "placeholder": "Ex: Cachorro"})
        self.fields["raca"].widget.attrs.update({"class": base, "placeholder": "Ex: SRD"})

        self.fields["status"].widget.attrs.update({"class": base})
        self.fields["sexo"].widget.attrs.update({"class": base})
        self.fields["porte"].widget.attrs.update({"class": base})

        self.fields["idade_anos"].widget.attrs.update({"class": base, "placeholder": "Ex: 5"})
        self.fields["idade_meses"].widget.attrs.update({"class": base, "placeholder": "0 a 11"})

        self.fields["historia"].widget.attrs.update({"class": base, "placeholder": "Conte uma breve história, temperamento, cuidados..."})
        self.fields["foto"].widget.attrs.update({"class": base})

        # checkboxes mais bonitos
        check = "h-5 w-5 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
        self.fields["vacinado"].widget.attrs.update({"class": check})
        self.fields["castrado"].widget.attrs.update({"class": check})

BASE_INPUT = "w-full rounded-xl border border-gray-300 bg-gray-50 px-3 py-2.5 focus:outline-none focus:ring-4 focus:ring-emerald-200 focus:border-emerald-600 transition"

class SolicitarTipoForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["solicitacao_tipo", "ong_cnpj", "ong_representante_legal"]

    def clean(self):
        cleaned = super().clean()
        tipo = (cleaned.get("solicitacao_tipo") or "").upper()

        if tipo == "ADMIN":
            self.add_error("solicitacao_tipo", "Não é permitido solicitar ADMIN.")

        if tipo == "ONG":
            if not (cleaned.get("ong_cnpj") or "").strip():
                self.add_error("ong_cnpj", "Informe o CNPJ.")
            if not (cleaned.get("ong_representante_legal") or "").strip():
                self.add_error("ong_representante_legal", "Informe o representante legal.")

        return cleaned
    

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": BASE_INPUT, "placeholder": "seuemail@exemplo.com"}),
        }

class PerfilSettingsForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["telefone"]
        widgets = {
            "telefone": forms.TextInput(attrs={"class": BASE_INPUT, "placeholder": "(00) 00000-0000"}),
        }