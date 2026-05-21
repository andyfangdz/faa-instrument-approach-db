from datetime import datetime

from scrape_faa import download


class FakeResponse:
    def __init__(self, text="", content=b""):
        self.text = text
        self.content = content

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        yield self.content


def test_get_latest_release_number_handles_cifp_filename_without_underscore(
    monkeypatch,
):
    monkeypatch.setattr(
        download.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(
            """
            <a href="CIFP_260514.zip">CIFP_260514.zip</a>
            <a href="CIFP260611.zip">CIFP260611.zip</a>
            """
        ),
    )
    monkeypatch.setattr(
        download,
        "get_file_timestamp",
        lambda url: (
            datetime(2026, 6, 11)
            if url.endswith("CIFP260611.zip")
            else datetime(2026, 5, 14)
        ),
    )

    assert download.get_latest_release_number() == "260611"


def test_download_cifp_zip_uses_matching_faa_filename(monkeypatch, tmp_path):
    requested_urls = []

    def fake_get(url, *args, **kwargs):
        requested_urls.append(url)
        if url == download.CIFP_URL:
            return FakeResponse('<a href="CIFP260611.zip">CIFP260611.zip</a>')
        if url == f"{download.CIFP_URL}CIFP260611.zip":
            return FakeResponse(content=b"cifp zip")
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(download.requests, "get", fake_get)

    download.download_cifp_zip("260611", str(tmp_path))

    assert requested_urls == [
        download.CIFP_URL,
        f"{download.CIFP_URL}CIFP260611.zip",
    ]
    assert (tmp_path / "CIFP260611.zip").read_bytes() == b"cifp zip"
