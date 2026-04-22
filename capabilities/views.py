from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from capabilities.forms import CapabilityStateForm
from capabilities.models import CapabilityItem, CapabilityState, Cluster, Outlet


@login_required
def outlet_list(request):
    outlets = Outlet.objects.all()
    return render(request, "capabilities/outlet_list.html", {"outlets": outlets})


def _current_state_map(outlet):
    """Build {item_id: CapabilityState} with the latest row per item."""
    latest = {}
    for state in outlet.states.select_related("item", "set_by").order_by("-set_at"):
        if state.item_id not in latest:
            latest[state.item_id] = state
    return latest


@login_required
def outlet_detail(request, slug):
    outlet = get_object_or_404(Outlet, slug=slug)
    clusters = Cluster.objects.prefetch_related("items").order_by("order")
    current = _current_state_map(outlet)

    grid = []
    for cluster in clusters:
        rows = []
        for item in cluster.items.order_by("order", "name"):
            rows.append({"item": item, "state": current.get(item.id)})
        grid.append({"cluster": cluster, "rows": rows})

    history = (
        outlet.states
        .select_related("item", "item__cluster", "set_by", "source_diagnostic")
        .order_by("-set_at")[:20]
    )
    diagnostics = outlet.diagnostics.select_related("conducted_by").order_by("-date")[:10]

    return render(
        request,
        "capabilities/outlet_detail.html",
        {
            "outlet": outlet,
            "grid": grid,
            "history": history,
            "diagnostics": diagnostics,
        },
    )


@login_required
def capability_state_create(request, slug):
    outlet = get_object_or_404(Outlet, slug=slug)
    initial = {}
    item_id = request.GET.get("item")
    if item_id:
        initial["item"] = item_id

    if request.method == "POST":
        form = CapabilityStateForm(request.POST)
        if form.is_valid():
            state = form.save(commit=False)
            state.outlet = outlet
            state.set_by = request.user
            state.save()
            return redirect("capabilities:outlet_detail", slug=outlet.slug)
    else:
        form = CapabilityStateForm(initial=initial)

    return render(
        request,
        "capabilities/state_form.html",
        {"outlet": outlet, "form": form},
    )
