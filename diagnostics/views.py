from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from capabilities.models import Outlet
from diagnostics.forms import DiagnosticForm
from diagnostics.models import Diagnostic


@login_required
def diagnostic_create(request, slug):
    outlet = get_object_or_404(Outlet, slug=slug)

    if request.method == "POST":
        form = DiagnosticForm(request.POST)
        if form.is_valid():
            diagnostic = form.save(commit=False)
            diagnostic.outlet = outlet
            diagnostic.conducted_by = request.user
            diagnostic.save()
            return redirect("diagnostics:diagnostic_detail", pk=diagnostic.pk)
    else:
        form = DiagnosticForm()

    return render(
        request,
        "diagnostics/diagnostic_form.html",
        {"outlet": outlet, "form": form},
    )


@login_required
def diagnostic_detail(request, pk):
    diagnostic = get_object_or_404(
        Diagnostic.objects.select_related("outlet", "conducted_by"),
        pk=pk,
    )
    state_changes = diagnostic.state_changes.select_related("item", "item__cluster", "set_by").order_by("-set_at")
    return render(
        request,
        "diagnostics/diagnostic_detail.html",
        {"diagnostic": diagnostic, "state_changes": state_changes},
    )
