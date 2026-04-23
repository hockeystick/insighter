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


def _build_grid(clusters, current_state_by_item_id=None):
    """Group clusters → subclusters → items so the grid stays scannable at 90 items.

    Returns: [{cluster, subgroups: [{subcluster_name, rows: [{item, state?}]}]}]
    """
    grid = []
    for cluster in clusters:
        subgroups = []
        current_sub = None
        current_rows = None
        for item in cluster.items.order_by("order", "name"):
            sub = item.subcluster or "—"
            if sub != current_sub:
                current_rows = []
                subgroups.append({"subcluster": sub, "rows": current_rows})
                current_sub = sub
            row = {"item": item}
            if current_state_by_item_id is not None:
                row["state"] = current_state_by_item_id.get(item.id)
            current_rows.append(row)
        grid.append({"cluster": cluster, "subgroups": subgroups})
    return grid


@login_required
def outlet_detail(request, slug):
    outlet = get_object_or_404(Outlet, slug=slug)
    clusters = Cluster.objects.prefetch_related("items").order_by("order")
    current = _current_state_map(outlet)
    grid = _build_grid(clusters, current)

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


def taxonomy_browser(request):
    """Read-only taxonomy view. Intentionally public (no login) so demos can show
    the desk's working model without logging in. Shows no outlet or state data."""
    clusters = Cluster.objects.prefetch_related("items").order_by("order")
    grid = _build_grid(clusters)
    total_items = sum(c.items.count() for c in clusters)
    return render(
        request,
        "capabilities/taxonomy_browser.html",
        {"grid": grid, "cluster_count": len(grid), "item_count": total_items},
    )
