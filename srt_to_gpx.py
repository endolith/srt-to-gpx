import argparse
import os
import xml.etree.ElementTree as ET
from datetime import datetime


def parse_srt(file_path):
    """
    Parses an SRT file to extract GPS details: time, latitude, longitude, and elevation.

    Args:
        file_path (str): Path to the SRT file.

    Returns:
        list of dict: Extracted data with keys `time`, `lat`, `lon`, and `elevation`.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    entries = []
    for i in range(len(lines)):
        if '-->' in lines[i]:
            timestamp = lines[i + 1].strip()
            location_data = lines[i + 2].strip()
            try:
                lat, lon = map(float, location_data.split(",")[:2])
                elevation = location_data.split(
                    ",")[2].strip().replace("m", "")
                entries.append({
                    "time": timestamp,
                    "lat": lat,
                    "lon": lon,
                    "elevation": float(elevation)
                })
            except (ValueError, IndexError):
                raise ValueError("Invalid location data in file "
                                 f"{file_path}: {location_data}")
    return entries


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
    args = parser.parse_args()

    for srt_file in args.input_files:
        try:
            print(f"Processing {srt_file}...")
            srt_data = parse_srt(srt_file)
            output_file = os.path.join(
                args.output_dir, os.path.basename(
                    srt_file).replace(".srt", ".gpx")
            )
            generate_gpx(srt_data, output_file)
            validate_conversion(srt_data, output_file)
            print(f"Successfully converted {srt_file} to {output_file}")
        except Exception as e:
            print(f"Error processing {srt_file}: {e}")


if __name__ == "__main__":
    main()
