"""
This modules contains the neural network sub-classes that define the embedders for enelogic dataset.
"""
from pydantic import BaseModel

from ..nn_components import (
    CombinedEmbedder,
    ContextEmbedder,
    IntegerEmbedder,
    PositionEmbedder,
)
from ._registry import register_embedder


class _PositionEmbedderArgs(BaseModel):
    dim_embedding: int


class _IntegerEmbedderArgs(BaseModel):
    num_embedding: int
    dim_embedding: int
    dropout: float = 0.1
    quantize: bool = False
    quantize_max_val: float = 20000.0
    quantize_min_val: float = 0.0


class EnelogicEmbedderArgs(BaseModel):
    annual_consumption: _PositionEmbedderArgs
    month: _IntegerEmbedderArgs


@register_embedder("enelogic_label")
class EnelogicLabelEmbedder(CombinedEmbedder):
    def __init__(self, **kwargs):
        annual_consumption_embedder = PositionEmbedder(
            **kwargs["annual_consumption"],
        )
        month = IntegerEmbedder(
            **kwargs["month"],
        )

        super().__init__(
            dict_embedder={
                "annual_consumption": annual_consumption_embedder,
                "month": month,
            }
        )

    def forward(self, dict_labels: dict, **kwargs):
        return super().forward(dict_labels, **kwargs)


@register_embedder("enelogic_context")
class EnelogicContextEmbedder(ContextEmbedder):
    def __init__(self, **kwargs):
        annual_consumption_embedder = PositionEmbedder(
            **kwargs["annual_consumption"],
        )
        month = IntegerEmbedder(
            **kwargs["month"],
        )

        super().__init__(
            dict_embedder={
                "annual_consumption": annual_consumption_embedder,
                "month": month,
            }
        )

    def forward(self, dict_labels: dict, **kwargs):
        return super().forward(dict_labels, **kwargs)
