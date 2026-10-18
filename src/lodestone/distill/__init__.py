# SPDX-License-Identifier: Apache-2.0
"""Card distillation: heuristic fallback, LLM path, cache and rendering."""

from lodestone.distill.apply import (
    CardStats,
    apply_cards,
    contextualize_children,
    requeue_embeddings,
)
from lodestone.distill.heuristic import heuristic_card
from lodestone.distill.render import embedding_input, render_norm
from lodestone.distill.schema import Card

__all__ = [
    "Card",
    "CardStats",
    "apply_cards",
    "contextualize_children",
    "embedding_input",
    "heuristic_card",
    "render_norm",
    "requeue_embeddings",
]
