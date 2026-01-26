from __future__ import annotations

import logging
import os

import matplotlib as mpl
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import torch
from einops import rearrange


def plot_time_series_comparison(
    generated: torch.Tensor,
    real: torch.Tensor,
    output_path: str | None = None,
    title: str = "Time Series Comparison",
    mask: torch.Tensor | None = None,
    ymax: int | None = None,
    ymin: int | None = None,
    grid_generated_labels: list[str] | None = None,
    overlap_generated_label: str | None = None,
    layout: str = "overlap",  # New parameter: "overlap" or "grid"
    overlap_print_num_samples: bool = True,
) -> plt.figure:
    """
    Create a plot comparing generated and real time series data.

    Args:
        generated: Generated data tensor
        real: Real data tensor
        output_path: Path to save the plot
        title: Title for the plot
        mask: a 1d mask, length == data sequence length. 1 == grey, 0 == white.
        ymax: Maximum value for y-axis
        ymin: Minimum value for y-axis
        grid_generated_labels: the title text above each grid cell in generated data (grid layout)
        overlap_generated_label: the title text for the generated Axes (overlap layout)
        overlap_print_num_samples: whether to print how many samples are displayed (overlap layout)
        layout: Plot layout:
                - "overlap": all samples overlaid in two subplots (default)
                - "grid": each sample in its own subplot in a grid (max 4x4)
                  Falls back to "overlap" if too many samples
    """
    # Check mask
    if mask is not None:
        _data_seq_len = (
            generated.shape[1] * generated.shape[2]
            if generated.dim() == 3
            else generated.shape[1]
        )
        if len(mask) != _data_seq_len:
            raise ValueError("length of mask should be equal to data sequence length.")
        regions = process_mask(mask)

    # Apply custom style
    with plt.style.context("profile_generator.utils.article_compatible"):
        # Determine figure size
        _W, _H = plt.rcParams["figure.figsize"]
        rc_diag = (_W**2 + _H**2) ** 0.5
        # Common parameters
        dot_alpha_coef = 10  # Alpha coefficient for scatter dots
        line_alpha_coef = 72  # Alpha coefficient for lines

        # Function to get color based on daily consumption
        def _get_color(sample_day, _min_day_consumption, _max_day_consumption):
            line_cmap = mpl.cm.get_cmap("RdYlBu_r")
            _line_color_norm = mpl.colors.Normalize(
                vmin=_min_day_consumption, vmax=_max_day_consumption
            )
            return line_cmap(_line_color_norm(sample_day.sum()))

        # Process and flatten data
        def _preprocess_data(data):
            if data.dim() == 3:
                # If data is [batch, sequence, channel], flatten it to [batch, sequence*channel]
                return rearrange(data, "b s c -> b (s c)")
            return data

        # Function to plot mask regions on an axis
        def _plot_mask_regions(ax, data_vec_dim):
            if mask is not None:
                for _idx_region, (start, end) in enumerate(regions):
                    if _idx_region == len(regions) - 1:
                        ax.axvspan(
                            start, end, alpha=0.2, color="gray", label="Measured"
                        )
                        # only label the last region
                    else:
                        ax.axvspan(start, end, alpha=0.2, color="gray")
                    if start != 0:
                        ax.axvline(x=start, color="r", linestyle="--")
                    if end != data_vec_dim - 1:
                        ax.axvline(x=end, color="r", linestyle="--")

        # Set common axis properties
        def _set_axis_properties(ax, title_text, data_vec_dim):
            ax.set_xlabel("Time Step [-]")
            ax.set_ylabel("Normalized Power [-]")
            ax.set_xlim([0, data_vec_dim - 1])
            ax.set_ylim([ymin or -2, ymax or 2])
            ax.grid(True)
            ax.set_title(title_text)

        # Determine layout to use
        if layout == "grid":
            # For grid layout, determine if we have too many samples
            max_grid_size = 4
            max_plots = max_grid_size * max_grid_size - 1  # -1 for real sample

            if generated.shape[0] > max_plots:
                logging.warning(
                    f"Too many samples ({generated.shape[0]}) for grid layout. "
                    f"Switching to overlap layout."
                )
                layout = "overlap"

        # Create plots based on layout
        if layout == "overlap":
            if overlap_generated_label is None:
                overlap_generated_label = "Generated Samples"
            # Create figure with two subplots as in the original function
            _w, _h = 3, 2
            _w, _h = (
                (rc_diag / (_w**2 + _h**2) ** 0.5) * _w,
                (rc_diag / (_w**2 + _h**2) ** 0.5) * _h,
            )
            fig = plt.figure(figsize=(_w, _h))
            gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1], figure=fig)

            # Function to plot overlapping data
            def plot_overlapping_data(data, ax, title_text):
                data = _preprocess_data(data)

                # Limit number of samples to plot
                max_samples_to_plot = min(100, data.shape[0])
                data = data[:max_samples_to_plot]

                # Calculate daily consumption for coloring
                samples_daily_sum = data.sum(dim=1)
                # Sort by total consumption
                sample_idx = torch.argsort(samples_daily_sum, descending=True)
                    # plot highest consumption first (back)
                data = data[sample_idx]

                # Get statistics for coloring
                max_day_consumption = data.sum(dim=1).max().item()
                min_day_consumption = data.sum(dim=1).min().item()

                # Get data dimensions
                data_vec_dim = data.shape[1]

                # Plot each sample
                for index in range(max_samples_to_plot):
                    sample = data[index].cpu().numpy()
                    color = _get_color(
                        data[index], min_day_consumption, max_day_consumption
                    )

                    # Scatter plot
                    ax.scatter(
                        np.arange(data_vec_dim),
                        sample,
                        color=color,
                        s=0.5,
                        alpha=min(dot_alpha_coef / max_samples_to_plot, 1),
                        rasterized=True,
                    )

                    # Line plot
                    ax.plot(
                        np.arange(data_vec_dim),
                        sample,
                        linewidth=2.5,
                        color=color,
                        alpha=min(line_alpha_coef / max_samples_to_plot, 1),
                        rasterized=True,
                    )

                # Plot mask regions
                _plot_mask_regions(ax, data_vec_dim)

                # Set axis properties
                _set_axis_properties(ax, title_text, data_vec_dim)
                ax.legend()

            # Plot generated data
            ax_gen = fig.add_subplot(gs[0])
            if overlap_print_num_samples:
                overlap_generated_label += f" ({generated.shape[0]} "
                if generated.shape[0] > 1:
                    overlap_generated_label += "Samples)"
                else:
                    overlap_generated_label += "Sample)"
            plot_overlapping_data(
                generated,
                ax_gen,
                overlap_generated_label,
            )

            # Plot real data
            ax_real = fig.add_subplot(gs[1])
            _real_sample_title = "Real Samples"
            if overlap_print_num_samples:
                _real_sample_title += f" ({real.shape[0]} "
                if real.shape[0] > 1:
                    _real_sample_title += "Samples)"
                else:
                    _real_sample_title += "Sample)"
            plot_overlapping_data(
                real,
                ax_real,
                _real_sample_title,
            )

        elif layout == "grid":
            # For grid layout, show each sample in its own subplot

            # Check labels for each subplot
            if grid_generated_labels is not None and len(grid_generated_labels) != len(
                generated
            ):
                print(len(grid_generated_labels), len(generated), "uh huh")
                grid_generated_labels = None
            # Restrict real to just one sample if it has more
            if real.shape[0] > 1:
                real = real[:1]  # Take only the first sample
                logging.warning(
                    "Multiple real samples provided. Using only the first sample for grid layout."
                )

            # Preprocess data
            gen_data = _preprocess_data(generated)
            real_data = _preprocess_data(real)

            # Get data dimensions
            data_vec_dim = gen_data.shape[1]

            # Calculate statistics for consistent coloring across subplots
            all_data = torch.cat([gen_data, real_data], dim=0)
            _max_day_consumption = all_data.sum(dim=1).max().item()
            _min_day_consumption = all_data.sum(dim=1).min().item()

            # Determine the number of generated samples to show
            max_grid_size = 4
            max_plots = max_grid_size * max_grid_size - 1  # -1 for real sample
            num_gen_samples = min(max_plots, gen_data.shape[0])

            # Calculate grid dimensions
            total_plots = num_gen_samples + 1  # +1 for real sample
            grid_size = min(max_grid_size, int(np.ceil(np.sqrt(total_plots))))

            # Create figure
            _w, _h = 5, 4
            _w, _h = (
                (rc_diag / (_w**2 + _h**2) ** 0.5) * _w,
                (rc_diag / (_w**2 + _h**2) ** 0.5) * _h,
            )
            fig = plt.figure(figsize=(_w * grid_size, _h * grid_size))

            # Colors for grid layout
            REAL_COLOR = "blue"
            GENERATED_COLOR = "orange"

            # Function to plot a single sample
            def plot_single_sample(data, ax, title_text, is_real=False, idx=0):
                # Extract and plot the sample
                sample = data[idx].cpu().numpy()

                # Use simpler color scheme for grid layout
                color = REAL_COLOR if is_real else GENERATED_COLOR

                ax.plot(
                    np.arange(data_vec_dim),
                    sample,
                    linewidth=2.5,
                    color=color,
                    rasterized=True,
                )

                # Plot mask regions
                _plot_mask_regions(ax, data_vec_dim)

                # Set axis properties
                _set_axis_properties(ax, title_text, data_vec_dim)

            # Plot real sample in the first position
            ax_real = plt.subplot2grid((grid_size, grid_size), (0, 0))
            plot_single_sample(real_data, ax_real, "Real Sample", is_real=True)

            # Plot generated samples
            for i in range(num_gen_samples):
                # Calculate position in grid
                row = (i + 1) // grid_size
                col = (i + 1) % grid_size

                # Create subplot
                ax = plt.subplot2grid((grid_size, grid_size), (row, col))
                _title_text = (
                    f"Generated {i + 1}"
                    if grid_generated_labels is None
                    else grid_generated_labels[i]
                )
                plot_single_sample(gen_data, ax, _title_text, is_real=False, idx=i)

        else:
            raise ValueError(
                f"Unknown layout: {layout}. Choose from 'overlap' or 'grid'."
            )

        # Add overall title
        fig.suptitle(title, fontsize=16, fontweight="bold")

        # Save figure
        plt.tight_layout()
        if output_path is not None:
            if os.path.dirname(output_path) != "":  # if not empty
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches="tight")

            logging.info(f"Saved time series comparison plot to {output_path}")

        return fig


def process_mask(mask):
    """
    Process a binary mask to identify continuous regions where mask == 1.

    Parameters:
    -----------
    mask : array-like of 0s and 1s
        Binary mask array.

    Returns:
    --------
    regions : list of tuples
        List of (start_idx, end_idx) tuples for each continuous region where mask == 1.
    """
    mask = np.array(mask, dtype=int)
    regions = []
    in_region = False
    start_idx = None

    for i, val in enumerate(mask):
        if val == 1 and not in_region:
            # Start of a masked region
            start_idx = i
            in_region = True
        elif val == 0 and in_region:
            # End of a masked region
            regions.append((start_idx, i - 1))
            in_region = False

    # If the mask ends with 1, close the last region
    if in_region:
        regions.append((start_idx, len(mask) - 1))

    return regions
