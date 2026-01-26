"""
high level neural network backbone for EnergyDiff. 

Continuous Normalizing Flow (Diffusion) model.

This module contains the flow matching models, responsible for initializing, training, and checkpointing.
"""

import pytorch_lightning as pl
import torch
from ema_pytorch import EMA
from flow_matching.path import AffineProbPath, scheduler
from torch import Tensor

from .configuration import ModelConfig, TrainConfig
from .embedders import get_embedder
from .nn_components import DenoisingTransformer


class FlowModelPL(pl.LightningModule):
    """
    This class defines the Flow Matching model using PyTorch Lightning.
    """

    def __init__(
        self,
        model_config: ModelConfig | dict,
        train_config: TrainConfig | dict,
        num_in_channel: int,  # 1
        label_embedder_name: str | None = None,
        label_embedder_args: dict | None = None,
        context_embedder_name: str | None = None,
        context_embedder_args: dict | None = None,
    ):
        super().__init__()
        if isinstance(model_config, dict):
            model_config = ModelConfig(**model_config)
        if isinstance(train_config, dict):
            train_config = TrainConfig(**train_config)

        label_embedder = None
        if label_embedder_name is not None:
            _args = label_embedder_args or {}
            label_embedder = get_embedder(label_embedder_name, **_args)
        context_embedder = None
        if context_embedder_name is not None:
            _args = context_embedder_args or {}
            context_embedder = get_embedder(context_embedder_name, **_args)
        self.model = DenoisingTransformer(
            dim_base=model_config.dim_base,
            num_in_channel=num_in_channel,
            dim_out=num_in_channel,
            num_attn_head=model_config.num_attn_head,
            dim_feedforward=model_config.dim_feedforward,
            num_decoder_layer=model_config.num_encoder_layers,  # name mismatch, historical issue
            dropout=model_config.dropout,
            label_embedder=label_embedder,
            context_embedder=context_embedder,
        )
        self.num_in_channel = num_in_channel
        self.ema = EMA(
            self.model,
            beta=train_config.ema_decay,
            update_after_step=100,
            update_every=train_config.ema_update_every,
        )
        self.prediction_type = "velocity"
        self.path = AffineProbPath(
            scheduler=scheduler.CondOTScheduler(),
        )
        self.model_config = model_config
        self.train_config = train_config

        self.save_hyperparameters({
            "model_config": model_config.model_dump(),
            "train_config": train_config.model_dump(),
            "num_in_channel": num_in_channel,
            "label_embedder_name": label_embedder_name,
            "label_embedder_args": label_embedder_args,
            "context_embedder_name": context_embedder_name,
            "context_embedder_args": context_embedder_args,
        })  # NOTE manually add all hparams here

    def compile(self, *args, **kwargs):
        "Compile the model and EMA model. all arguments are passed to both `.compile`."
        self.model.compile(*args, **kwargs)
        self.ema.compile(*args, **kwargs)

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.train_config.lr,
            betas=self.train_config.adam_betas,
        )
        return optimizer

    def training_step(
        self,
        batch: tuple[Tensor, dict[str, Tensor]],  # profile, labels
        batch_idx: int,
    ):
        self.train()
        profile, labels = batch
        t = torch.rand(profile.shape[0]).to(profile.device)
        x_0 = torch.randn_like(profile)
        sample = self.path.sample(
            x_0=x_0,
            t=t,
            x_1=profile,
        )  # wraps x_t, dx_t, x_0, x_t, etc.
        target = sample.dx_t  # velocity target
        model_out = self.model(
            x=sample.x_t,
            t=t,
            c=labels,
        )
        loss = (model_out - target).pow(2).mean()
        self.log(
            "Train/loss",
            loss.item(),
            on_step=True,
            on_epoch=True,
            prog_bar=True,
            sync_dist=True,
        )

        return loss

    def on_train_batch_end(self, *args, **kwargs) -> None:
        self.ema.update()

    @torch.no_grad()
    def validation_step(self, batch, batch_idx) -> None:
        self.eval()
        profile, labels = batch
        t = torch.rand(profile.shape[0]).to(profile.device)
        x_0 = torch.randn_like(profile)
        sample = self.path.sample(
            x_0=x_0,
            t=t,
            x_1=profile,
        )  # wraps x_t, dx_t, x_0, x_t, etc.
        target = sample.dx_t  # velocity target
        model_out = self.model(
            x=sample.x_t,
            t=t,
            c=labels,
        )
        loss = (model_out - target).pow(2).mean()
        self.log(
            "Validation/loss",
            loss.item(),
            on_step=False,
            on_epoch=True,
            prog_bar=True,
            sync_dist=True,
        )
