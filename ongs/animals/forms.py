from django import forms
from .models import Animal


class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = ["nome", "especie", "raca", "foto"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        base = "w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
        self.fields["nome"].widget.attrs.update({"class": base, "placeholder": "Ex: Bob"})
        self.fields["especie"].widget.attrs.update({"class": base, "placeholder": "Ex: Cachorro"})
        self.fields["raca"].widget.attrs.update({"class": base, "placeholder": "Ex: SRD"})
        self.fields["foto"].widget.attrs.update({"class": base})
