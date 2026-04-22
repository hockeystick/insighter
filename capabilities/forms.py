from django import forms

from capabilities.models import CapabilityItem, CapabilityState


class CapabilityStateForm(forms.ModelForm):
    class Meta:
        model = CapabilityState
        fields = ["item", "level", "evidence_excerpt", "source_diagnostic"]
        widgets = {
            "evidence_excerpt": forms.Textarea(attrs={"rows": 4, "class": "w-full border rounded p-2"}),
            "item": forms.Select(attrs={"class": "w-full border rounded p-2"}),
            "level": forms.Select(attrs={"class": "w-full border rounded p-2"}),
            "source_diagnostic": forms.Select(attrs={"class": "w-full border rounded p-2"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = CapabilityItem.objects.select_related("cluster").order_by(
            "cluster__order", "order", "name"
        )
        self.fields["source_diagnostic"].required = False
