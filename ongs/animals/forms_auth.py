from allauth.account.forms import LoginForm, SignupForm
from django.utils.translation import gettext_lazy as _
from django import forms

class CustomLoginForm(LoginForm):
    def clean(self):
        try:
            return super().clean()
        except forms.ValidationError as e:
            codes = {getattr(err, "code", "") for err in getattr(e, "error_list", [])}
            msg = " ".join([str(err) for err in getattr(e, "error_list", [])])

            if "invalid_login" in codes or "not correct" in msg.lower():
                raise forms.ValidationError(_("E-mail e/ou senha incorretos."))
            raise

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["login"].widget.attrs.update({
            "placeholder": "Digite seu e-mail",
        })

        self.fields["password"].widget.attrs.update({
            "placeholder": "Digite sua senha",
        })


class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "email" in self.fields:
            self.fields["email"].widget.attrs.update({
                "placeholder": "Digite seu e-mail",
            })

        if "password1" in self.fields:
            self.fields["password1"].widget.attrs.update({
                "placeholder": "Crie uma senha",
            })

        if "password2" in self.fields:
            self.fields["password2"].widget.attrs.update({
                "placeholder": "Confirme sua senha",
            })

        if "username" in self.fields:
            self.fields["username"].widget = forms.HiddenInput()
            self.fields["username"].required = False

    def save(self, request):
        user = super().save(request)
        if not user.username:
            user.username = user.email
            user.save(update_fields=["username"])
        return user