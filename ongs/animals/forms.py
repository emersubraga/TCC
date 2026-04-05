import re
import json
from urllib import request as urlrequest, error as urlerror

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Animal, Perfil


def only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def is_valid_cpf(cpf: str) -> bool:
    cpf = only_digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    d1 = 0 if d1 == 10 else d1
    if d1 != int(cpf[9]):
        return False

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
            "nome","especie","raca",
            "status","sexo","porte",
            "idade_anos","idade_meses",
            "vacinado","castrado",
            "historia",
            "foto",
        ]


BASE_INPUT = "w-full rounded-xl border border-gray-300 bg-gray-50 px-3 py-2.5 focus:outline-none focus:ring-4 focus:ring-emerald-200 focus:border-emerald-600 transition"


class SolicitarTipoForm(forms.ModelForm):

    protetor_cpf = forms.CharField(
        required=False,
        label="CPF",
        max_length=14,
        widget=forms.TextInput(attrs={
            "class": BASE_INPUT,
            "placeholder": "000.000.000-00"
        })
    )

    class Meta:
        model = Perfil
        fields = [
            "solicitacao_tipo",
            "protetor_cpf",
            "ong_cnpj",
            "ong_representante_legal"
        ]

        widgets = {
            "solicitacao_tipo": forms.Select(attrs={"class": BASE_INPUT}),
            "ong_cnpj": forms.TextInput(attrs={
                "class": BASE_INPUT,
                "placeholder": "00.000.000/0000-00"
            }),
            "ong_representante_legal": forms.TextInput(attrs={
                "class": BASE_INPUT,
                "placeholder": "Nome do representante legal"
            }),
        }

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("solicitacao_tipo")

        cpf = cleaned.get("protetor_cpf")
        cnpj = cleaned.get("ong_cnpj")
        rep = cleaned.get("ong_representante_legal")

        if tipo == "PROTETOR":
            if not cpf:
                self.add_error("protetor_cpf","Informe o CPF.")
            elif not is_valid_cpf(cpf):
                self.add_error("protetor_cpf","CPF inválido.")

        if tipo == "ONG":
            if not cnpj:
                self.add_error("ong_cnpj","Informe o CNPJ.")
            elif not is_valid_cnpj(cnpj):
                self.add_error("ong_cnpj","CNPJ inválido.")

            if not rep:
                self.add_error("ong_representante_legal","Informe o representante legal.")

        return cleaned


class UserSettingsForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ["username","email"]

        widgets = {
            "username": forms.TextInput(attrs={
                "class": BASE_INPUT,
                "placeholder": "Nome de usuário"
            }),

            "email": forms.EmailInput(attrs={
                "class": BASE_INPUT,
                "placeholder": "seuemail@exemplo.com"
            }),
        }


class PerfilSettingsForm(forms.ModelForm):

    class Meta:
        model = Perfil
        fields = ["telefone"]

        widgets = {
            "telefone": forms.TextInput(attrs={
                "class": BASE_INPUT,
                "placeholder": "(00) 00000-0000"
            }),
        }