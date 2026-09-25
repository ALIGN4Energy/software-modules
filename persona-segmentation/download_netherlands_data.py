#!/usr/bin/env python3
"""
Download the open data that persona_assignment.Rmd reads.

- CBS "Kerncijfers per postcode": PC6, PC5 and PC4 for the demographics year,
  PC5 and PC4 for the income year. Only the .xlsx inside each zip is kept.
- BAG: bag-light.gpkg from PDOK (about 8 GB).

Files that already exist are skipped, so the script can be re-run safely.

Usage: python3 download_netherlands_data.py [DATA_DIR] [CBS_YEAR] [INCOME_YEAR]
Defaults: ./data, 2025, 2023
"""

import io
import sys
import zipfile
from pathlib import Path

import requests

CBS_URL = "https://download.cbs.nl/postcode/{release}-cbs_pc{level}_{year}_{version}.zip"
BAG_URL = "https://service.pdok.nl/lv/bag/atom/downloads/bag-light.gpkg"

# CBS publishes a year three times: v1 one year later, v2 two years later and
# the final "vol" three years later. The most final version wins.
VERSIONS = [("vol", 3), ("v2", 2), ("v1", 1)]


def download_cbs(data_dir, level, year):
    existing = sorted(data_dir.glob(f"pc{level}_{year}_*.xlsx"))
    if existing:
        print(f"✓ {existing[0].name} already present")
        return True

    for version, offset in VERSIONS:
        url = CBS_URL.format(release=year + offset, level=level, year=year, version=version)
        response = requests.get(url, timeout=300)
        if response.status_code == 404:
            continue
        response.raise_for_status()

        name = f"pc{level}_{year}_{version}.xlsx"
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            (data_dir / name).write_bytes(archive.read(name))
        print(f"✓ Downloaded {name}")
        return True

    print(f"✗ No CBS PC{level} file found for {year}")
    return False


def download_bag(data_dir):
    target = data_dir / "bag-light.gpkg"
    if target.exists():
        print(f"✓ {target.name} already present")
        return True

    print("Downloading bag-light.gpkg (about 8 GB, this takes a while)...")
    partial = target.with_suffix(".gpkg.part")
    with requests.get(BAG_URL, stream=True, timeout=300) as response:
        response.raise_for_status()
        with open(partial, "wb") as file:
            for chunk in response.iter_content(chunk_size=1 << 20):
                file.write(chunk)
    partial.rename(target)
    print(f"✓ Downloaded {target.name}")
    return True


def main():
    data_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
    cbs_year = int(sys.argv[2]) if len(sys.argv) > 2 else 2025
    income_year = int(sys.argv[3]) if len(sys.argv) > 3 else 2023
    data_dir.mkdir(parents=True, exist_ok=True)

    print(f"Open data for persona assignment -> {data_dir.absolute()}")
    print(f"CBS demographics year {cbs_year}, income year {income_year}")

    ok = all([
        download_cbs(data_dir, 6, cbs_year),
        download_cbs(data_dir, 5, cbs_year),
        download_cbs(data_dir, 4, cbs_year),
        download_cbs(data_dir, 5, income_year),
        download_cbs(data_dir, 4, income_year),
        download_bag(data_dir),
    ])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
