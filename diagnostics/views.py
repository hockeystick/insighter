from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from capabilities.models import CapabilityItem, CapabilityState
from diagnostics.forms import DiagnosticForm
from diagnostics.models import Diagnostic
from insighter.llm.client import has_api_key
from insighter.llm.synthesis import run_synthesis


_LEVEL_STR_TO_INT = {
    "Unknown": CapabilityState.LEVEL_UNKNOWN,
    "Aware": CapabilityState.LEVEL_AWARE,
    "Practising": CapabilityState.LEVEL_PRACTISING,
    "Embedded": CapabilityState.LEVEL_EMBEDDED,
}
_LEVEL_CHOICES = ["Unknown", "Aware", "Practising", "Embedded"]


@login_required
def diagnostic_create(request, slug):
    from capabilities.models import Outlet

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
    state_changes = diagnostic.state_changes.select_related(
        "item", "item__cluster", "set_by"
    ).order_by("-set_at")
    return render(
        request,
        "diagnostics/diagnostic_detail.html",
        {
            "diagnostic": diagnostic,
            "state_changes": state_changes,
            "has_api_key": has_api_key(),
            "has_proposals": bool(diagnostic.llm_proposals_json),
        },
    )


@login_required
@require_POST
def synthesis_run(request, pk):
    """Call Claude to synthesise state-change proposals from the diagnostic notes."""
    diagnostic = get_object_or_404(Diagnostic, pk=pk)
    if not has_api_key():
        return render(
            request,
            "diagnostics/synthesis_error.html",
            {
                "diagnostic": diagnostic,
                "error": "ANTHROPIC_API_KEY is not set in the environment.",
            },
            status=503,
        )

    try:
        result = run_synthesis(diagnostic)
    except Exception as exc:  # surface errors directly in demo mode
        return render(
            request,
            "diagnostics/synthesis_error.html",
            {"diagnostic": diagnostic, "error": f"{type(exc).__name__}: {exc}"},
            status=502,
        )

    diagnostic.llm_proposals_json = result
    diagnostic.save(update_fields=["llm_proposals_json", "updated_at"])
    return redirect("diagnostics:synthesis_review", pk=diagnostic.pk)


@login_required
def synthesis_review(request, pk):
    diagnostic = get_object_or_404(
        Diagnostic.objects.select_related("outlet", "conducted_by"),
        pk=pk,
    )
    payload = diagnostic.llm_proposals_json or {}
    raw_proposals = list(payload.get("proposals", []))

    item_ids = [p["item_id"] for p in raw_proposals if isinstance(p.get("item_id"), int)]
    items = {
        i.id: i
        for i in CapabilityItem.objects.filter(id__in=item_ids).select_related("cluster")
    }

    latest_by_item: dict[int, CapabilityState] = {}
    for state in (
        diagnostic.outlet.states.filter(item_id__in=item_ids)
        .select_related("item")
        .order_by("-set_at")
    ):
        if state.item_id not in latest_by_item:
            latest_by_item[state.item_id] = state

    rows = []
    for proposal in raw_proposals:
        item = items.get(proposal.get("item_id"))
        if item is None:
            continue
        rows.append(
            {
                "proposal": proposal,
                "item": item,
                "current": latest_by_item.get(item.id),
                "level_choices": _LEVEL_CHOICES,
            }
        )

    return render(
        request,
        "diagnostics/synthesis_review.html",
        {
            "diagnostic": diagnostic,
            "rows": rows,
            "usage": payload.get("usage", {}),
            "model": payload.get("model", ""),
        },
    )


@login_required
@require_POST
def synthesis_accept(request, pk):
    diagnostic = get_object_or_404(Diagnostic, pk=pk)
    payload = diagnostic.llm_proposals_json or {}
    proposals_by_id = {
        str(p["item_id"]): p
        for p in payload.get("proposals", [])
        if isinstance(p.get("item_id"), int)
    }

    accepted = 0
    for item_id_str, proposal in proposals_by_id.items():
        action = request.POST.get(f"action_{item_id_str}", "reject")
        if action != "accept":
            continue
        level_str = request.POST.get(f"level_{item_id_str}", proposal.get("proposed_level", "Unknown"))
        champion = request.POST.get(f"champion_{item_id_str}") == "on"
        evidence = request.POST.get(
            f"evidence_{item_id_str}", proposal.get("evidence_excerpt", "")
        ).strip()
        if not evidence:
            continue

        CapabilityState.objects.create(
            outlet=diagnostic.outlet,
            item_id=int(item_id_str),
            level=_LEVEL_STR_TO_INT.get(level_str, CapabilityState.LEVEL_UNKNOWN),
            led_by_champion=champion,
            evidence_excerpt=evidence,
            set_by=request.user,
            source_diagnostic=diagnostic,
            llm_proposed=True,
            accepted_by=request.user,
        )
        accepted += 1

    if accepted > 0 and diagnostic.status != Diagnostic.STATUS_COMMITTED:
        diagnostic.status = Diagnostic.STATUS_COMMITTED
        diagnostic.save(update_fields=["status", "updated_at"])

    return redirect("capabilities:outlet_detail", slug=diagnostic.outlet.slug)
