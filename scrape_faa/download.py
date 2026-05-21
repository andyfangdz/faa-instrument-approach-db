import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime


CIFP_URL = "https://aeronav.faa.gov/Upload_313-d/cifp/"
DTPP_URL = "https://aeronav.faa.gov/upload_313-d/terminal/"
CIFP_ZIP_PATTERN = re.compile(r"^CIFP_?(\d{6})\.zip$", re.IGNORECASE)
REQUEST_TIMEOUT = (10, 60)
DOWNLOAD_CHUNK_SIZE = 1024 * 1024 * 8
DOWNLOAD_PROGRESS_INTERVAL = 1024 * 1024 * 100


def format_bytes(byte_count: int) -> str:
    for unit in ["B", "KB", "MB"]:
        if byte_count < 1024:
            return f"{byte_count:.1f} {unit}"
        byte_count /= 1024
    return f"{byte_count:.1f} GB"


def get_cifp_release_number(filename: str) -> str | None:
    match = CIFP_ZIP_PATTERN.match(filename)
    if match is None:
        return None
    return match.group(1)


def get_cifp_zip_links():
    response = requests.get(CIFP_URL, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    zip_links = []
    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        filename = os.path.basename(urlparse(href).path)
        release_number = get_cifp_release_number(filename)
        if release_number is None:
            filename = link.getText().strip()
            release_number = get_cifp_release_number(filename)
        if release_number is None:
            continue

        zip_links.append((filename, urljoin(CIFP_URL, href), release_number))

    return zip_links


def get_latest_release_number() -> str:
    # Uses the CIFP url to get the latest d-TPP release number like
    # 250320, 250417, etc.
    print(f"Fetching page: {CIFP_URL}", flush=True)
    zip_links = get_cifp_zip_links()
    print("Page retrieved successfully.", flush=True)
    print("Parsing HTML content...", flush=True)

    # Get the timestamp for each zip file and store them in a list
    zip_files_with_timestamps = []
    for zip_file, zip_url, release_number in zip_links:
        timestamp = get_file_timestamp(zip_url)
        zip_files_with_timestamps.append((zip_file, release_number, timestamp))

    if not zip_files_with_timestamps:
        raise RuntimeError("No CIFP zip files found.")

    # Sort the zip files by the timestamp (latest first)
    zip_files_with_timestamps.sort(key=lambda x: x[2], reverse=True)
    latest_zip_file, latest_release_number, _ = zip_files_with_timestamps[0]

    print(f"Latest CIFP file found: {latest_zip_file}", flush=True)
    # Convert CIFP_250123.zip or CIFP250123.zip to 250123
    return latest_release_number


def download_file(url: str, filename: str):
    download_dir = os.path.dirname(filename)
    if download_dir:
        os.makedirs(download_dir, exist_ok=True)

    print(f"Downloading {url}...", flush=True)
    response = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    total_bytes = int(response.headers.get("Content-Length") or 0)
    if total_bytes:
        print(f"Expected size: {format_bytes(total_bytes)}", flush=True)

    bytes_written = 0
    next_progress = DOWNLOAD_PROGRESS_INTERVAL
    with open(filename, "wb") as file:
        for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
            if not chunk:
                continue

            file.write(chunk)
            bytes_written += len(chunk)
            if total_bytes and bytes_written >= next_progress:
                percentage = (bytes_written / total_bytes) * 100
                print(
                    f"Downloaded {format_bytes(bytes_written)} of "
                    f"{format_bytes(total_bytes)} ({percentage:.1f}%).",
                    flush=True,
                )
                while next_progress <= bytes_written:
                    next_progress += DOWNLOAD_PROGRESS_INTERVAL

    if total_bytes and bytes_written != total_bytes:
        raise RuntimeError(
            f"Incomplete download for {url}: expected {total_bytes} bytes, "
            f"received {bytes_written} bytes."
        )

    print(f"Downloaded: {filename} ({format_bytes(bytes_written)})", flush=True)


def download_cifp_zip(release_number: str, download_folder: str):
    zip_links = get_cifp_zip_links()
    latest_zip_link = None
    latest_zip_filename = None
    for zip_filename, zip_link, zip_release_number in zip_links:
        if zip_release_number == release_number:
            latest_zip_link = zip_link
            latest_zip_filename = zip_filename
            break

    if latest_zip_link is None:
        latest_zip_filename = f"CIFP_{release_number}.zip"
        latest_zip_link = urljoin(CIFP_URL, latest_zip_filename)

    filename = os.path.join(download_folder, latest_zip_filename)
    download_file(latest_zip_link, filename)


def download_dtpp_zips(release_number: str, download_folder: str):
    print(f"Fetching page: {DTPP_URL}", flush=True)
    response = requests.get(DTPP_URL, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    print("Page retrieved successfully.", flush=True)

    soup = BeautifulSoup(response.text, "html.parser")
    print("Parsing HTML content...", flush=True)

    # Extract all .zip links involving the current release number
    zip_links = [
        urljoin(DTPP_URL, link["href"])
        for link in soup.find_all("a", href=True)
        if link["href"].endswith(".zip") and release_number in link["href"]
    ]

    print(f"Found {len(zip_links)} d-TPP zip files for {release_number}.", flush=True)

    for zip_url in zip_links:
        zip_name = os.path.join(download_folder, os.path.basename(zip_url))
        download_file(zip_url, zip_name)


# Function to get the timestamp of a file using the 'Last-Modified' header
def get_file_timestamp(url):
    # Send a HEAD request to get the headers of the file
    response = requests.head(url, timeout=REQUEST_TIMEOUT)
    return datetime.strptime(
        response.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z"
    )


if __name__ == "__main__":
    latest_release = get_latest_release_number()

    # Set the release number as an output if we're running on CI.
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"release={latest_release}\n")

    download_cifp_zip(latest_release, "download")
    download_dtpp_zips(latest_release, "download")
