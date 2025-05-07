import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime


CIFP_URL = "https://aeronav.faa.gov/Upload_313-d/cifp/"
DTPP_URL = "https://aeronav.faa.gov/upload_313-d/terminal/"


def get_latest_release_number() -> str:
    # Uses the CIFP url to get the latest d-TPP release number like
    # 250320, 250417, etc.
    print(f"Fetching page: {CIFP_URL}")
    response = requests.get(CIFP_URL, timeout=10)
    response.raise_for_status()
    print("Page retrieved successfully.")

    soup = BeautifulSoup(response.text, "html.parser")
    print("Parsing HTML content...")

    # Extract all .zip links
    zip_files = [
        link.getText()
        for link in soup.find_all("a", href=True)
        if link["href"].endswith(".zip")
    ]

    # Get the timestamp for each zip file and store them in a list
    zip_files_with_timestamps = []
    for zip_file in zip_files:
        zip_url = urljoin(CIFP_URL, zip_file)
        timestamp = get_file_timestamp(zip_url)
        zip_files_with_timestamps.append((zip_file, timestamp))

    # Sort the zip files by the timestamp (latest first)
    zip_files_with_timestamps.sort(key=lambda x: x[1], reverse=True)
    latest_zip_file = zip_files_with_timestamps[0][0]

    print(f"Latest CIFP file found: {latest_zip_file}")
    # Convert CIFP_250123.zip to 250123
    return latest_zip_file.replace("CIFP_", "").replace(".zip", "")


def download_cifp_zip(release_number: str, download_folder: str):
    latest_zip_link = urljoin(CIFP_URL, f"CIFP_{release_number}.zip")

    # Download the latest zip file
    filename = os.path.join(download_folder, os.path.basename(latest_zip_link))
    os.makedirs(download_folder, exist_ok=True)

    print(f"Downloading {latest_zip_link}...")
    zip_response = requests.get(latest_zip_link, stream=True, timeout=10)
    zip_response.raise_for_status()
    with open(filename, "wb") as file:
        for chunk in zip_response.iter_content(chunk_size=1024 * 20):
            file.write(chunk)
    print(f"Downloaded: {filename}")


def download_dtpp_zips(release_number: str, download_folder: str):
    print(f"Fetching page: {DTPP_URL}")
    response = requests.get(DTPP_URL, timeout=10)
    response.raise_for_status()
    print("Page retrieved successfully.")

    soup = BeautifulSoup(response.text, "html.parser")
    print("Parsing HTML content...")

    # Extract all .zip links involving the current release number
    zip_links = [
        urljoin(DTPP_URL, link["href"])
        for link in soup.find_all("a", href=True)
        if link["href"].endswith(".zip") and release_number in link["href"]
    ]

    for zip_url in zip_links:
        print(f"Downloading: {zip_url}")
        zip_response = requests.get(zip_url, stream=True, timeout=10)
        zip_response.raise_for_status()

        zip_name = os.path.join(download_folder, os.path.basename(zip_url))
        with open(zip_name, "wb") as file:
            for chunk in zip_response.iter_content(chunk_size=1024 * 20):
                file.write(chunk)


# Function to get the timestamp of a file using the 'Last-Modified' header
def get_file_timestamp(url):
    # Send a HEAD request to get the headers of the file
    response = requests.head(url)
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
