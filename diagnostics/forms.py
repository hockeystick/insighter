from django import forms

from diagnostics.models import Diagnostic


class DiagnosticForm(forms.ModelForm):
    class Meta:
        model = Diagnostic
        fields = ["date", "notes_raw", "notes_summary"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "border rounded p-2"}),
            "notes_raw": forms.Textarea(attrs={"rows": 10, "class": "w-full border rounded p-2 font-mono text-sm"}),
            "notes_summary": forms.Textarea(attrs={"rows": 3, "class": "w-full border rounded p-2 text-sm"}),
        }
