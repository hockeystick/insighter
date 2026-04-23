"""Thin wrapper around the Anthropic SDK.

Reads ANTHROPIC_API_KEY from the environment (SDK default). Centralises the
model ID and effort so callers don't drift.
"""
from __future__ import annotations

import os

from anthropic import Anthropic

MODEL = "claude-opus-4-7"
EFFORT = "xhigh"
MAX_TOKENS = 8192


def has_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def get_client() -> Anthropic:
    return Anthropic()
