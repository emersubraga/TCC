from allauth.account.forms import LoginForm, SignupForm
from django.utils.translation import gettext_lazy as _
from django import forms

class CustomLoginForm(LoginForm):
    def clean(self):
        try:
            return super().clean()
        except forms.ValidationError as e:
            # tenta identificar o erro de login inválido
            codes = {getattr(err, "code", "") for err in getattr(e, "error_list", [])}
            msg = " ".join([str(err) for err in getattr(e, "error_list", [])])

            if "invalid_login" in codes or "not correct" in msg.lower():
                raise forms.ValidationError(_("Usuário e/ou senha incorretos."))
            raise

class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({
            "placeholder": "Escolha um nome de usuário",
        })

        self.fields["email"].widget.attrs.update({
            "placeholder": "Digite seu e-mail",
        })

        self.fields["password1"].widget.attrs.update({
            "placeholder": "Crie uma senha",
        })

        self.fields["password2"].widget.attrs.update({
            "placeholder": "Confirme sua senha",
        })