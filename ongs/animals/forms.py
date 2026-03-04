import re
from django import forms
from .models import Animal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Perfil

def only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def is_valid_cpf(cpf: str) -> bool:
    cpf = only_digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    # dígito 1
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    d1 = 0 if d1 == 10 else d1
    if d1 != int(cpf[9]):
        return False
    # dígito 2
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    d2 = 0 if d2 == 10 else d2
    return d2 == int(cpf[10])

def is_valid_cnpj(cnpj: str) -> bool:
    cnpj = only_digits(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def calc_dv(numeros, pesos):
        s = sum(int(numeros[i]) * pesos[i] for i in range(len(pesos)))
        r = s % 11
        return "0" if r < 2 else str(11 - r)

    pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    pesos2 = [6] + pesos1

    dv1 = calc_dv(cnpj[:12], pesos1)
    dv2 = calc_dv(cnpj[:12] + dv1, pesos2)
    return cnpj[-2:] == dv1 + dv2

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
    protetor_cpf = forms.CharField(
        required=False,
        label="CPF",
        max_length=14,
        widget=forms.TextInput(attrs={"placeholder": "000.000.000-00"})
    )

    class Meta:
        model = Perfil
        fields = ["solicitacao_tipo", "protetor_cpf", "ong_cnpj", "ong_representante_legal"]

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("solicitacao_tipo")

        cpf = cleaned.get("protetor_cpf")
        cnpj = cleaned.get("ong_cnpj")
        rep = cleaned.get("ong_representante_legal")

        # COMUM: não exige nada
        if tipo == "COMUM":
            cleaned["protetor_cpf"] = ""
            cleaned["ong_cnpj"] = ""
            cleaned["ong_representante_legal"] = ""
            return cleaned

        # PROTETOR: exige CPF válido
        if tipo == "PROTETOR":
            if not cpf:
                self.add_error("protetor_cpf", _("Informe o CPF."))
            elif not is_valid_cpf(cpf):
                self.add_error("protetor_cpf", _("CPF inválido."))
            cleaned["ong_cnpj"] = ""
            cleaned["ong_representante_legal"] = ""
            return cleaned

        # ONG: exige CNPJ válido + representante
        if tipo == "ONG":
            if not cnpj:
                self.add_error("ong_cnpj", _("Informe o CNPJ."))
            elif not is_valid_cnpj(cnpj):
                self.add_error("ong_cnpj", _("CNPJ inválido."))
            if not rep:
                self.add_error("ong_representante_legal", _("Informe o representante legal."))
            cleaned["protetor_cpf"] = ""
            return cleaned

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