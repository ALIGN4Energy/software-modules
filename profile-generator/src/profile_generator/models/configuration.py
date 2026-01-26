"""
This module contains the configuration classes for the flow matching models.

author: Nan Lin
"""
from pydantic import BaseModel


class ModelConfig(BaseModel):
    "nn model and flow model"
    dim_base: int
    dim_feedforward: int = 2048
    num_attn_head: int = 4
    dropout: float = 0.1
    num_encoder_layers: int = 6
    num_in_channel: int | None = None  # added runtime
    num_parameter: int | None = None  # added runtime


class TrainConfig(BaseModel):
    batch_size: int
    lr: float = 1e-4
    adam_betas: tuple[float, float] = (0.9, 0.999)
    ema_update_every: int = 5
    ema_decay: float = 0.9999
    num_train_step: int = 100000
    save_and_sample_every: int = 50000
    val_sampling_step: int = 100
    val_every: int = 2500
    gradient_accumulate_every: int = 1