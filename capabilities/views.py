from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from capabilities.forms import CapabilityStateForm
from capabilities.models import CapabilityItem, CapabilityState, Cluster, Outlet
from insighter.llm.client import has_api_key


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
    """Group clusters → subclusters → items so the grid stays scannable at 90 items."""
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


def _bus_factor_summary(outlet, current_state_map):
    """Cheap, deterministic bus-factor indicators — no LLM."""
    states = list(current_state_map.values())
    champion_count = sum(1 for s in states if s.led_by_champion)
    embedded_count = sum(
        1 for s in states if s.level == CapabilityState.LEVEL_EMBEDDED
    )
    last_change = (
        outlet.states.order_by("-set_at").values_list("set_at", flat=True).first()
    )
    return {
        "has_data_champion": outlet.data_champion is not None,
        "champion_count": champion_count,
        "embedded_count": embedded_count,
        "recorded_items": len(states),
        "last_change_at": last_change,
    }


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
    """Read-only taxonomy — intentionally public for demos."""
    clusters = Cluster.objects.prefetch_related("items").order_by("order")
    grid = _build_grid(clusters)
    total_items = sum(c.items.count() for c in clusters)
    return render(
        request,
        "capabilities/taxonomy_browser.html",
        {"grid": grid, "cluster_count": len(grid), "item_count": total_items},
    )


@login_required
def why_stuck(request, slug):
    """Single composed view: capability state summary, recent diagnostics,
    cached mismatch flag, bus-factor indicators. No live LLM call — the
    mismatch is rendered from the last cached run (button to refresh)."""
    outlet = get_object_or_404(Outlet, slug=slug)
    clusters = Cluster.objects.prefetch_related("items").order_by("order")
    current = _current_state_map(outlet)

    # Per-cluster rollup: count of items at each level
    cluster_rollups = []
    for cluster in clusters:
        counts = {"Unknown": 0, "Aware": 0, "Practising": 0, "Embedded": 0, "no signal": 0}
        cluster_items = list(cluster.items.all())
        for item in cluster_items:
            state = current.get(item.id)
            if state is None:
                counts["no signal"] += 1
            else:
                counts[state.get_level_display()] += 1
        cluster_rollups.append({
            "cluster": cluster,
            "counts": counts,
            "no_signal": counts["no signal"],
            "total": len(cluster_items),
        })

    recent_history = (
        outlet.states
        .select_related("item", "item__cluster", "set_by")
        .order_by("-set_at")[:10]
    )
    diagnostics = outlet.diagnostics.select_related("conducted_by").order_by("-date")[:3]

    bus_factor = _bus_factor_summary(outlet, current)

    return render(
        request,
        "capabilities/why_stuck.html",
        {
            "outlet": outlet,
            "cluster_rollups": cluster_rollups,
            "recent_history": recent_history,
            "diagnostics": diagnostics,
            "bus_factor": bus_factor,
            "mismatch": outlet.mismatch_flag_json,
            "mismatch_computed_at": outlet.mismatch_flag_computed_at,
            "has_api_key": has_api_key(),
        },
    )


@login_required
@require_POST
def mismatch_run(request, slug):
    outlet = get_object_or_404(Outlet, slug=slug)
    if not has_api_key():
        return render(
            request,
            "capabilities/mismatch_error.html",
            {"outlet": outlet, "error": "ANTHROPIC_API_KEY is not set in the environment."},
            status=503,
        )

    from insighter.llm.mismatch import run_mismatch

    try:
        result = run_mismatch(outlet)
    except Exception as exc:
        return render(
            request,
            "capabilities/mismatch_error.html",
            {"outlet": outlet, "error": f"{type(exc).__name__}: {exc}"},
            status=502,
        )

    outlet.mismatch_flag_json = result
    outlet.mismatch_flag_computed_at = timezone.now()
    outlet.save(update_fields=["mismatch_flag_json", "mismatch_flag_computed_at"])
    return redirect("capabilities:why_stuck", slug=outlet.slug)
