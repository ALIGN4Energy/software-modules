#!/usr/bin/env python3
"""
CLI script for generating annual energy consumption profiles.

This script generates daily energy consumption profiles for all 12 months based on
household characteristics and technology adoption.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from profile_generator.interfaces.demo_model.config import (
    DemoModelConfig,
    DemoSampleConfig,
    DemoSampleCondition,
    Month,
)
from profile_generator.interfaces.demo_model.model import DemoModel


MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate annual energy consumption profiles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic household with 6500 kWh annual consumption
  python generate_profile_cli.py --annual_consumption 6500 --output profile.json

  # Household with heat pump
  python generate_profile_cli.py --annual_consumption 7500 --has_heatpump true --output profile.json

  # Household with solar panels and heat pump
  python generate_profile_cli.py --annual_consumption 8000 --has_heatpump true --has_solar true --output profile.json

  # All technologies
  python generate_profile_cli.py \\
    --annual_consumption 9000 \\
    --has_heatpump true \\
    --has_solar true \\
    --has_ev true \\
    --output profile.json

Output:
  JSON file containing daily profiles (96 intervals × 15 minutes) for all 12 months
        """
    )

    # Required parameter
    parser.add_argument(
        '--annual_consumption',
        type=float,
        required=True,
        help='Annual energy consumption in kWh (required)'
    )

    # Technology parameters
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

    # Output configuration
    parser.add_argument(
        '--output',
        type=str,
        default='output/profile.json',
        help='Output file path (default: output/profile.json)'
    )

    parser.add_argument(
        '--model_path',
        type=str,
        default='tests/models/demo_model_state_dict.pt',
        help='Path to trained model file (default: tests/models/demo_model_state_dict.pt)'
    )

    return parser.parse_args()


def str_to_bool(value: str) -> bool:
    """Convert string to boolean"""
    return value.lower() in ['true', '1']


def generate_annual_profiles(
    model: DemoModel,
    annual_consumption: float,
    has_heatpump: bool,
    has_solar: bool,
    has_ev: bool
) -> dict:
    """
    Generate daily profiles for all 12 months.

    Args:
        model: Loaded profile generator model
        annual_consumption: Annual energy consumption in kWh
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
            "model_info": "Demo model - full model will incorporate technology parameters"
        },
        "profiles": []
    }

    # Generate profile for each month
    for month_idx in range(12):
        # Note: Current demo model only uses month and annual_consumption
        # The real trained model will also use has_heatpump, has_solar, has_ev
        sample_config = DemoSampleConfig(batch_size=1)
        sample_condition = DemoSampleCondition(
            month=Month(month_idx),
            annual_consumption=annual_consumption
        )

        # Generate profile (96 intervals × 15 minutes = 24 hours)
        profile = model.sample(sample_config, sample_condition)
        profile_list = profile[0].cpu().numpy().tolist()

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

    # Convert string booleans
    has_heatpump = str_to_bool(args.has_heatpump)
    has_solar = str_to_bool(args.has_solar)
    has_ev = str_to_bool(args.has_ev)

    # Validate inputs
    if args.annual_consumption <= 0:
        print("Error: annual_consumption must be positive", file=sys.stderr)
        sys.exit(1)

    # Print configuration
    print("=== PROFILE GENERATION STARTING ===")
    print(f"Annual consumption: {args.annual_consumption} kWh")
    print(f"Heat pump: {has_heatpump}")
    print(f"Solar panels: {has_solar}")
    print(f"Electric vehicle: {has_ev}")
    print(f"Output: {args.output}")
    print()

    # Load model
    try:
        print(f"Loading model from {args.model_path}...")
        model = DemoModel(DemoModelConfig(model_path=args.model_path))
        print("Model loaded successfully")
    except Exception as e:
        print(f"Error loading model: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate profiles
    print("\nGenerating profiles for 12 months...")
    try:
        profiles_data = generate_annual_profiles(
            model=model,
            annual_consumption=args.annual_consumption,
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

    print(f"  Average consumption: {sum(all_means) / len(all_means):.2f}")
    print(f"  Min consumption: {min(all_mins):.2f}")
    print(f"  Max consumption: {max(all_maxs):.2f}")

    print("\n=== GENERATION COMPLETED ===")


if __name__ == "__main__":
    main()
