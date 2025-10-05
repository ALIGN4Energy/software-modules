#!/usr/bin/env python3
"""
Script to download CBS postcode files and 3DBAG data.
Downloads and extracts: pc6_2023_v2.xlsx, pc5_2023_v2.xlsx, pc4_2023_v2.xlsx
Downloads: bag_data.csv from 3DBAG API (bag_id, oppervlakte_m2, bouwjaar)
"""

import requests
import os
import zipfile
import json
import csv
from pathlib import Path

def download_and_extract_zip(url, zip_filename):
    """Download a ZIP file and extract its contents."""
    print(f"Downloading {zip_filename}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(zip_filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        print(f"✓ Downloaded {zip_filename} ({os.path.getsize(zip_filename)} bytes)")
        
        # Extract the ZIP file
        print(f"Extracting {zip_filename}...")
        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
            zip_ref.extractall('.')
            extracted_files = zip_ref.namelist()
            print(f"✓ Extracted: {', '.join(extracted_files)}")
        
        # Remove the ZIP file after extraction
        os.remove(zip_filename)
        
        return True, extracted_files
        
    except (requests.RequestException, zipfile.BadZipFile) as e:
        print(f"✗ Failed to download or extract {zip_filename}: {e}")
        return False, []

def download_csv(url, filename):
    """Download a CSV file directly."""
    print(f"Downloading {filename}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        print(f"✓ Downloaded {filename} ({os.path.getsize(filename)} bytes)")
        return True
        
    except requests.RequestException as e:
        print(f"✗ Failed to download {filename}: {e}")
        return False

def download_3dbag_data(filename="bag_data.csv", limit=1000):
    """Download 3DBAG building data via API and save as CSV."""
    print(f"Downloading 3DBAG building data (limit: {limit})...")
    
    try:
        # 3DBAG API endpoint for building data
        api_url = f"https://api.3dbag.nl/collections/pand/items?limit={limit}"
        
        response = requests.get(api_url)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract features and write to CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['bag_id', 'oppervlakte_m2', 'bouwjaar']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            buildings_written = 0
            for feature in data.get('features', []):
                # The building data is in CityObjects
                city_objects = feature.get('CityObjects', {})
                
                for obj_id, obj_data in city_objects.items():
                    if obj_data.get('type') == 'Building':
                        attributes = obj_data.get('attributes', {})
                        
                        # Extract the fields we want
                        bag_id = attributes.get('identificatie') or obj_id
                        oppervlakte = attributes.get('b3_opp_grond')  # Ground surface area
                        bouwjaar = attributes.get('oorspronkelijkbouwjaar')
                        
                        if bag_id:  # Only write if we have a bag_id
                            writer.writerow({
                                'bag_id': bag_id,
                                'oppervlakte_m2': oppervlakte if oppervlakte else '',
                                'bouwjaar': bouwjaar if bouwjaar else ''
                            })
                            buildings_written += 1
        
        print(f"✓ Downloaded 3DBAG data: {buildings_written} buildings saved to {filename}")
        print(f"  File size: {os.path.getsize(filename)} bytes")
        return True
        
    except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"✗ Failed to download 3DBAG data: {e}")
        return False

def main():
    """Main function to download CBS postcode files and 3DBAG data."""
    # CBS postcode ZIP files
    zip_downloads = [
        ("https://download.cbs.nl/postcode/2025-cbs_pc6_2023_v2.zip", "pc6_2023_v2.zip"),
        ("https://download.cbs.nl/postcode/2025-cbs_pc5_2023_v2.zip", "pc5_2023_v2.zip"),
        ("https://download.cbs.nl/postcode/2025-cbs_pc4_2023_v2.zip", "pc4_2023_v2.zip")
    ]
    
    
    print("CBS Postcode Files & 3DBAG Data Downloader")
    print("=" * 50)
    
    # Create downloads directory if it doesn't exist
    download_dir = Path("cbs_postcode_data")
    download_dir.mkdir(exist_ok=True)
    os.chdir(download_dir)
    
    # Download CBS ZIP files
    print("\n📦 Downloading CBS postcode ZIP files...")
    zip_success_count = 0
    all_extracted_files = []
    
    for url, zip_filename in zip_downloads:
        success, extracted_files = download_and_extract_zip(url, zip_filename)
        if success:
            zip_success_count += 1
            all_extracted_files.extend(extracted_files)
    
    # Download 3DBAG data via API
    print("\n📊 Downloading 3DBAG building data...")
    csv_success = download_3dbag_data("bag_data.csv", limit=5000)
    
    # Summary
    print(f"\n✅ Summary:")
    print(f"CBS archives: {zip_success_count}/{len(zip_downloads)} processed successfully")
    print(f"3DBAG CSV: {'✓' if csv_success else '✗'}")
    print(f"Files saved to: {download_dir.absolute()}")
    
    if all_extracted_files:
        print(f"CBS extracted files: {', '.join(all_extracted_files)}")
    if csv_success:
        print("3DBAG file: bag_data.csv")

if __name__ == "__main__":
    main()