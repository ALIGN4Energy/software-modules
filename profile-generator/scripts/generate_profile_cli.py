#!/usr/bin/env python3
# Copyright Contributors to the ALIGN4Energy Project.
# SPDX-License-Identifier: Apache-2.0

# The EnergyDiff model is made available via Nan Lin and Pedro P. Vergara
# from the Delft University of Technology. Nan Lin and Pedro P. Vergara are
# funded via the ALIGN4Energy Project (with project number NWA.1389.20.251) of
# the research programme NWA ORC 2020 which is (partly) financed by the Dutch
# Research Council (NWO), The Netherland.

"""
CLI script for generating annual energy consumption profiles using the EnergyDiff model.

This script generates daily energy consumption profiles for all 12 months based on
household characteristics using a flow-matching based diffusion model.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from profile_generator.interfaces.energydiff.config import (
    EnergyDiffModelConfig,
    EnergyDiffSampleConfig,
    EnergyDiffSampleCondition,
    Month,
)
from profile_generator.interfaces.energydiff.model import EnergyDiffModel


MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate annual energy consumption profiles using EnergyDiff model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic household with 6500 kWh annual consumption
  python generate_profile_cli.py --model_path /path/to/model.ckpt --annual_consumption 6500 --output profile.json

  # Household with heat pump (higher consumption)
  python generate_profile_cli.py --model_path /path/to/model.ckpt --annual_consumption 7500 --has_heatpump true --output profile.json

  # Household with solar panels and heat pump
  python generate_profile_cli.py --model_path /path/to/model.ckpt --annual_consumption 8000 --has_heatpump true --has_solar true --output profile.json

  # All technologies with custom diffusion steps
  python generate_profile_cli.py \\
    --model_path /path/to/model.ckpt \\
    --annual_consumption 9000 \\
    --has_heatpump true \\
    --has_solar true \\
    --has_ev true \\
    --num_steps 200 \\
    --output profile.json

Output:
  JSON file containing daily profiles (96 intervals × 15 minutes) for all 12 months
        """
    )

    # Required parameters
    parser.add_argument(
        '--model_path',
        type=str,
        required=True,
        help='Path to trained EnergyDiff model checkpoint (.ckpt file) (required)'
    )

    parser.add_argument(
        '--annual_consumption',
        type=float,
        required=True,
        help='Annual energy consumption in kWh (required)'
    )

    # Technology parameters (for metadata, model conditioning to be added)
    parser.add_argument(
        '--has_heatpump',
        type=str,
        default='false',
        choices=['true', 'false', 'True', 'False', '1', '0'],
        help='Household has heat pump (default: false)'
    )

    parser.add_argument(
        '--has_solar',
        type=str,
        default='false',
        choices=['true', 'false', 'True', 'False', '1', '0'],
        help='Household has solar panels (default: false)'
    )

    parser.add_argument(
        '--has_ev',
        type=str,
        default='false',
        choices=['true', 'false', 'True', 'False', '1', '0'],
        help='Household has electric vehicle (default: false)'
    )

    # Model parameters
    parser.add_argument(
        '--num_steps',
        type=int,
        default=200,
        help='Number of diffusion steps for sampling (default: 200)'
    )

    parser.add_argument(
        '--device',
        type=str,
        default='cpu',
        choices=['cpu', 'cuda', 'mps'],
        help='Device to run the model on (default: cpu)'
    )

    # Output configuration
    parser.add_argument(
        '--output',
        type=str,
        default='output/profile.json',
        help='Output file path (default: output/profile.json)'
    )

    return parser.parse_args()


def str_to_bool(value: str) -> bool:
    """Convert string to boolean"""
    return value.lower() in ['true', '1']


def generate_annual_profiles(
    model: EnergyDiffModel,
    annual_consumption: float,
    num_steps: int,
    has_heatpump: bool,
    has_solar: bool,
    has_ev: bool
) -> dict:
    """
    Generate daily profiles for all 12 months.

    Args:
        model: Loaded EnergyDiff model
        annual_consumption: Annual energy consumption in kWh
        num_steps: Number of diffusion steps
        has_heatpump: Whether household has heat pump
        has_solar: Whether household has solar panels
        has_ev: Whether household has electric vehicle

    Returns:
        Dictionary with metadata and monthly profiles
    """
    profiles_data = {
        "metadata": {
            "annual_consumption": annual_consumption,
            "has_heatpump": has_heatpump,
            "has_solar": has_solar,
            "has_ev": has_ev,
            "generated_at": datetime.now().isoformat(),
            "model_info": "EnergyDiff flow-matching model",
            "num_steps": num_steps
        },
        "profiles": []
    }

    # Generate profile for each month
    for month_idx in range(12):
        sample_config = EnergyDiffSampleConfig(batch_size=1, num_steps=num_steps)
        sample_condition = EnergyDiffSampleCondition(
            month=Month(month_idx),
            annual_consumption=annual_consumption
        )

        # Generate profile (96 intervals × 15 minutes = 24 hours)
        profile = model.sample(sample_config, sample_condition)
        # Output shape is (batch_size, 96, 1), squeeze to get (96,)
        profile_list = profile[0].squeeze(-1).cpu().numpy().tolist()

        profiles_data["profiles"].append({
            "month": month_idx + 1,
            "month_name": MONTH_NAMES[month_idx],
            "daily_profile": profile_list,
            "statistics": {
                "min": min(profile_list),
                "max": max(profile_list),
                "mean": sum(profile_list) / len(profile_list),
                "intervals": len(profile_list)
            }
        })

    return profiles_data


def main():
    """Main execution function"""
    args = parse_args()

    # Validate model path exists
    model_path = Path(args.model_path)
    if not model_path.exists():
        print(f"""
Error: Model checkpoint not found at '{args.model_path}'

The EnergyDiff model requires a trained checkpoint file (.ckpt).
Please ensure you have:

1. A valid EnergyDiff model checkpoint file
2. The correct path to the checkpoint

Example usage:
  python generate_profile_cli.py \\
    --model_path /path/to/energydiff_model.ckpt \\
    --annual_consumption 6500 \\
    --output profile.json

For more information, see the README.md file.
""", file=sys.stderr)
        sys.exit(1)

    # Convert string booleans
    has_heatpump = str_to_bool(args.has_heatpump)
    has_solar = str_to_bool(args.has_solar)
    has_ev = str_to_bool(args.has_ev)

    # Validate inputs
    if args.annual_consumption <= 0:
        print("Error: annual_consumption must be positive", file=sys.stderr)
        sys.exit(1)

    if args.num_steps <= 0:
        print("Error: num_steps must be positive", file=sys.stderr)
        sys.exit(1)

    # Print configuration
    print("=== ENERGYDIFF PROFILE GENERATION STARTING ===")
    print(f"Model: {args.model_path}")
    print(f"Annual consumption: {args.annual_consumption} kWh")
    print(f"Heat pump: {has_heatpump}")
    print(f"Solar panels: {has_solar}")
    print(f"Electric vehicle: {has_ev}")
    print(f"Diffusion steps: {args.num_steps}")
    print(f"Device: {args.device}")
    print(f"Output: {args.output}")
    print()

    # Load model
    try:
        print(f"Loading EnergyDiff model from {args.model_path}...")
        model = EnergyDiffModel(EnergyDiffModelConfig(
            model_path=str(args.model_path),
            device=args.device
        ))
        print("Model loaded successfully")
    except Exception as e:
        print(f"""
Error loading model: {e}

Please ensure:
1. The checkpoint file is a valid EnergyDiff model (.ckpt)
2. The file is not corrupted
3. You have the required dependencies installed (pytorch-lightning, flow-matching, etc.)
""", file=sys.stderr)
        sys.exit(1)

    # Generate profiles
    print("\nGenerating profiles for 12 months...")
    try:
        profiles_data = generate_annual_profiles(
            model=model,
            annual_consumption=args.annual_consumption,
            num_steps=args.num_steps,
            has_heatpump=has_heatpump,
            has_solar=has_solar,
            has_ev=has_ev
        )
    except Exception as e:
        print(f"Error generating profiles: {e}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to JSON
    try:
        with open(output_path, 'w') as f:
            json.dump(profiles_data, f, indent=2)
        print(f"\nProfiles saved to {args.output}")
    except Exception as e:
        print(f"Error saving output: {e}", file=sys.stderr)
        sys.exit(1)

    # Print summary
    print("\n=== GENERATION SUMMARY ===")
    print(f"Months generated: 12")
    print(f"Intervals per day: 96 (15-minute resolution)")
    print(f"Total data points: {12 * 96}")
    print("\nProfile statistics (average across all months):")

    all_means = [p["statistics"]["mean"] for p in profiles_data["profiles"]]
    all_mins = [p["statistics"]["min"] for p in profiles_data["profiles"]]
    all_maxs = [p["statistics"]["max"] for p in profiles_data["profiles"]]

    print(f"  Average consumption: {sum(all_means) / len(all_means):.4f}")
    print(f"  Min consumption: {min(all_mins):.4f}")
    print(f"  Max consumption: {max(all_maxs):.4f}")

    print("\n=== GENERATION COMPLETED ===")


if __name__ == "__main__":
    main()
