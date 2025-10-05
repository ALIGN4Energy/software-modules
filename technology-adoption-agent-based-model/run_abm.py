#!/usr/bin/env python3
"""
Wrapper script to run the Energy Technology Adoption ABM with configurable parameters.
"""

import argparse
import sys
import os
import pandas as pd
import numpy as np
from ABM import run_monte_carlo_simulation

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Run Energy Technology Adoption Agent-Based Model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic run with tutorial data
  python run_abm.py --household_data tutorial_households.csv --tech_config tutorial_technologies.csv

  # Custom Monte Carlo runs and years
  python run_abm.py --household_data tutorial_households.csv --tech_config tutorial_technologies.csv --n_runs 50 --years 15

  # No policy support scenario
  python run_abm.py --household_data tutorial_households.csv --tech_config tutorial_technologies.csv --policy false

  # Vary peer effect strength
  python run_abm.py --household_data tutorial_households.csv --tech_config tutorial_technologies.csv --peer_effect 0.5

  # Combined options
  python run_abm.py --household_data my_data.csv --tech_config my_tech.csv --n_runs 200 --years 20 --policy true --peer_effect 0.3
        """
    )

    parser.add_argument(
        '--n_runs',
        type=int,
        default=100,
        help='Number of Monte Carlo simulation runs (default: 100)'
    )

    parser.add_argument(
        '--years',
        type=int,
        default=10,
        help='Number of simulation years per run (default: 10)'
    )

    parser.add_argument(
        '--policy',
        type=str,
        default='true',
        choices=['true', 'false', 'True', 'False', '1', '0'],
        help='Enable policy support (default: true)'
    )

    parser.add_argument(
        '--peer_effect',
        type=float,
        default=0.2,
        help='Peer effect strength 0-1 (default: 0.2)'
    )

    parser.add_argument(
        '--household_data',
        type=str,
        required=True,
        help='Path to household data CSV (required)'
    )

    parser.add_argument(
        '--tech_config',
        type=str,
        required=True,
        help='Path to technology config CSV (required)'
    )

    parser.add_argument(
        '--output_dir',
        type=str,
        default='output',
        help='Output directory for results (default: output)'
    )

    return parser.parse_args()


def str_to_bool(value):
    """Convert string to boolean"""
    return value.lower() in ['true', '1']


def main():
    """Main execution function"""
    args = parse_args()

    # Convert policy string to boolean
    policy_support = str_to_bool(args.policy)

    # Validate inputs
    if args.n_runs <= 0:
        print("Error: n_runs must be positive", file=sys.stderr)
        sys.exit(1)

    if args.years <= 0:
        print("Error: years must be positive", file=sys.stderr)
        sys.exit(1)

    if not 0 <= args.peer_effect <= 1:
        print("Error: peer_effect must be between 0 and 1", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.household_data):
        print(f"Error: Household data file not found: {args.household_data}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.tech_config):
        print(f"Error: Technology config file not found: {args.tech_config}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Print configuration
    print("=== ABM SIMULATION STARTING ===")
    print(f"Monte Carlo runs: {args.n_runs}")
    print(f"Simulation years: {args.years}")
    print(f"Policy support: {policy_support}")
    print(f"Peer effect strength: {args.peer_effect}")
    print(f"Household data: {args.household_data}")
    print(f"Technology config: {args.tech_config}")
    print(f"Output directory: {args.output_dir}")
    print()

    # Run Monte Carlo simulation
    print("Running Monte Carlo simulation...")
    try:
        mc_results = run_monte_carlo_simulation(
            n_runs=args.n_runs,
            years=args.years,
            csv_file_path=args.household_data,
            tech_config_path=args.tech_config,
            policy_support=policy_support,
            peer_effect_strength=args.peer_effect
        )
    except FileNotFoundError as e:
        print(f"\nError: Required file not found: {e}", file=sys.stderr)
        print(f"Please check that the following files exist:", file=sys.stderr)
        print(f"  - Household data: {args.household_data}", file=sys.stderr)
        print(f"  - Technology config: {args.tech_config}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\nError: Invalid data format: {e}", file=sys.stderr)
        print(f"Please check that your CSV files have the correct structure.", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"\nError: Missing required column in data: {e}", file=sys.stderr)
        print(f"Please check your CSV file structure matches the expected schema.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError during simulation: {e}", file=sys.stderr)
        print(f"Simulation failed. Please check your input data and parameters.", file=sys.stderr)
        sys.exit(1)

    # Get technology names from config
    try:
        config_df = pd.read_csv(args.tech_config)
        technology_names = config_df['technology'].tolist()
    except Exception as e:
        print(f"\nError reading technology config: {e}", file=sys.stderr)
        sys.exit(1)

    # Save detailed results
    results_path = os.path.join(args.output_dir, 'monte_carlo_results.csv')
    mc_results.to_csv(results_path, index=False)
    print(f"\nDetailed results saved to: {results_path}")

    # Calculate and print summary statistics
    summary_path = os.path.join(args.output_dir, 'summary_statistics.txt')
    with open(summary_path, 'w') as f:
        f.write("=== MONTE CARLO RESULTS ===\n")
        f.write(f"Runs: {args.n_runs}\n")
        f.write(f"Years: {args.years}\n")
        f.write(f"Policy Support: {policy_support}\n")
        f.write(f"Peer Effect: {args.peer_effect}\n")
        f.write("\n")
        f.write("=== OVERALL ADOPTION RATES ===\n")

        print("\n=== MONTE CARLO RESULTS ===")
        print(f"Runs: {args.n_runs}, Years: {args.years}")
        print(f"Policy Support: {policy_support}, Peer Effect: {args.peer_effect}")
        print("\n=== OVERALL ADOPTION RATES ===")

        for tech_name in technology_names:
            mean_rate = mc_results[f'{tech_name}_adoption_rate'].mean()
            std_rate = mc_results[f'{tech_name}_adoption_rate'].std()
            ci_lower = np.percentile(mc_results[f'{tech_name}_adoption_rate'], 2.5)
            ci_upper = np.percentile(mc_results[f'{tech_name}_adoption_rate'], 97.5)

            tech_display = tech_name.replace('_', ' ').title()
            line = f"{tech_display}: {mean_rate:.3f} ± {std_rate:.3f} [95% CI: {ci_lower:.3f}-{ci_upper:.3f}]"
            print(line)
            f.write(line + "\n")

        f.write("\n=== ADOPTION BY LATENT CLASS ===\n")
        print("\n=== ADOPTION BY LATENT CLASS ===")

        class_names = {
            1: "Class 1 - Financially driven (~12.9%)",
            2: "Class 2 - Policy driven (~17.3%)",
            3: "Class 3 - Erratic choosers (~13.1%)",
            4: "Class 4 - Comfort driven (~56.7%)"
        }

        for class_id in [1, 2, 3, 4]:
            size_mean = mc_results[f'class_{class_id}_size'].mean()
            header = f"\n{class_names[class_id]} (avg size: {size_mean:.0f})"
            print(header)
            f.write(header + "\n")

            for tech_name in technology_names:
                mean = mc_results[f'class_{class_id}_{tech_name}_rate'].mean()
                std = mc_results[f'class_{class_id}_{tech_name}_rate'].std()
                ci_lower = np.percentile(mc_results[f'class_{class_id}_{tech_name}_rate'], 2.5)
                ci_upper = np.percentile(mc_results[f'class_{class_id}_{tech_name}_rate'], 97.5)

                tech_display = tech_name.replace('_', ' ').title()
                line = f"  {tech_display}: {mean:.3f} ± {std:.3f} [95% CI: {ci_lower:.3f}-{ci_upper:.3f}]"
                print(line)
                f.write(line + "\n")

    print(f"\nSummary statistics saved to: {summary_path}")
    print("\n=== SIMULATION COMPLETED ===")


if __name__ == "__main__":
    main()
