import argparse
import os
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime


def parse_srt(file_path):
    """
    Parses an SRT file to extract GPS details: time, latitude, longitude, and elevation.

    Args:
        file_path (str): Path to the SRT file.

    Returns:
        tuple: A list of valid entries (dict) and a count of skipped invalid entries.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    entries = []
    skipped = 0
    for i in range(len(lines)):
        if '-->' in lines[i]:
            timestamp = lines[i + 1].strip()
            location_data = lines[i + 2].strip()
            try:
                if ',' in location_data:
                    lat, lon = map(float, location_data.split(",")[:2])
                    elevation = location_data.split(
                        ",")[2].strip().replace("m", "")
                    entries.append({
                        "time": timestamp,
                        "lat": lat,
                        "lon": lon,
                        "elevation": float(elevation)
                    })
                else:
                    skipped += 1  # Skip compass heading-only entries
            except (ValueError, IndexError):
                skipped += 1
    return entries, skipped


def convert_to_iso8601(date_str):
    """
    Converts a date string to ISO 8601 format.

    Args:
        date_str (str): Date string in the format `Jul 4, 2024 6:13:17 PM`.

    Returns:
        str: ISO 8601 formatted string.
    """
    try:
        parsed_time = datetime.strptime(date_str, "%b %d, %Y %I:%M:%S %p")
        return parsed_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError(f"Invalid time format: {date_str}")


def generate_gpx(data, output_file):
    """
    Generates a GPX file from parsed SRT data.

    Args:
        data (list of dict): Parsed SRT data.
        output_file (str): Path to save the GPX file.
    """
    gpx = ET.Element(
        "gpx",
        version="1.1",
        creator="SRTtoGPX",
        xmlns="http://www.topografix.com/GPX/1/1",
    )

    # Add metadata
    metadata = ET.SubElement(gpx, "metadata")
    ET.SubElement(metadata, "name").text = "SRT to GPX Converter"
    ET.SubElement(
        metadata, "desc").text = "Converted using OpenCamera SRT to GPX Script"
    ET.SubElement(metadata, "author").text = "OpenCamera Script"
    ET.SubElement(metadata, "time").text = datetime.utcnow().strftime(
        "%Y-%m-%dT%H:%M:%SZ")

    trk = ET.SubElement(gpx, "trk")
    trkseg = ET.SubElement(trk, "trkseg")

    for entry in data:
        trkpt = ET.SubElement(trkseg, "trkpt", lat=str(
            entry["lat"]), lon=str(entry["lon"]))
        ET.SubElement(trkpt, "ele").text = str(entry["elevation"])
        ET.SubElement(trkpt, "time").text = convert_to_iso8601(entry["time"])

    tree = ET.ElementTree(gpx)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)


def validate_conversion(srt_data, gpx_file):
    """
    Validates that the GPX file matches the original SRT data.

    Args:
        srt_data (list of dict): Original parsed SRT data.
        gpx_file (str): Path to the GPX file.

    Raises:
        AssertionError: If validation fails.
    """
    tree = ET.parse(gpx_file)
    root = tree.getroot()
    namespace = {"ns": "http://www.topografix.com/GPX/1/1"}

    trkpts = root.findall(".//ns:trkpt", namespace)
    assert len(srt_data) == len(trkpts), "Mismatch in number of points."

    for srt_point, trkpt in zip(srt_data, trkpts):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        ele = float(trkpt.find("ns:ele", namespace).text)
        time = trkpt.find("ns:time", namespace).text

        assert (srt_point["lat"], srt_point["lon"]) == (
            lat, lon), "Mismatch in coordinates."
        assert srt_point["elevation"] == ele, "Mismatch in elevation."
        assert convert_to_iso8601(
            srt_point["time"]) == time, "Mismatch in time."


def set_file_modification_time(gpx_file, reference_file):
    """
    Sets the modification time of the GPX file to match the reference file.

    Args:
        gpx_file (str): Path to the GPX file.
        reference_file (str): Path to the reference file (e.g., SRT file).
    """
    ref_stat = os.stat(reference_file)
    os.utime(gpx_file, (ref_stat.st_atime, ref_stat.st_mtime))


def main():
    parser = argparse.ArgumentParser(
        description="Convert SRT files with GPS data to GPX format."
    )
    parser.add_argument(
        "input_files", nargs="+", help="Path to one or more SRT files to convert."
    )
    parser.add_argument(
        "--output_dir", default=".", help="Directory to save the GPX files."
    )
    parser.add_argument(
        "--no-match-time", action="store_true",
        dest="no_match_time",
        help="Do not set the GPX file's modification time to match the SRT file. By default, it is matched."
    )
    args = parser.parse_args()

    for srt_file in args.input_files:
        try:
            print(f"Processing {srt_file}...")
            srt_data, skipped = parse_srt(srt_file)

            if not srt_data:
                print(f"No GPS data found in file: {srt_file}. Only compass "
                      "headings or invalid entries were present.")
                continue

            output_file = os.path.join(
                args.output_dir, os.path.basename(
                    srt_file).replace(".srt", ".gpx")
            )
            generate_gpx(srt_data, output_file)
            validate_conversion(srt_data, output_file)

            if not args.no_match_time:
                set_file_modification_time(output_file, srt_file)

            print(f"Successfully converted {srt_file} to {output_file}")
            print(f"Skipped {skipped} invalid or non-GPS entries.")
        except Exception as e:
            print(f"Error processing {srt_file}: {e}")


if __name__ == "__main__":
    main()
