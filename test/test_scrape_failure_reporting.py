import zipfile

import pytest

from plate_analyzer import scrape_faa_dtpp_zip


@pytest.fixture
def analyze_worker_results(tmp_path, monkeypatch):
    metadata = """
        <digital_tpp>
            <airport_name icao_ident="KAAA">
                <record>
                    <chart_code>IAP</chart_code>
                    <pdf_name>FIRST.PDF</pdf_name>
                    <chart_name>ILS RWY 01</chart_name>
                    <civil>Y</civil>
                </record>
            </airport_name>
            <airport_name icao_ident="KBBB">
                <record>
                    <chart_code>IAP</chart_code>
                    <pdf_name>SECOND.PDF</pdf_name>
                    <chart_name>RNAV RWY 02</chart_name>
                    <civil>Y</civil>
                </record>
            </airport_name>
        </digital_tpp>
    """
    with zipfile.ZipFile(tmp_path / "DDTPPE_260903.zip", "w") as archive:
        archive.writestr("d-TPP_Metafile.xml", metadata)

    monkeypatch.setattr(scrape_faa_dtpp_zip, "analyze_cifp_file", lambda path: {})

    def analyze(results):
        class FakePool:
            def __init__(self, processes):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def imap_unordered(self, function, inputs):
                return iter(results)

        monkeypatch.setattr(scrape_faa_dtpp_zip.multiprocessing, "Pool", FakePool)
        return scrape_faa_dtpp_zip.analyze_dtpp_zips(
            tmp_path, cifp_file="unused", num_worker_processes=1
        )

    return analyze


def test_first_worker_failure_is_reported_without_crashing(analyze_worker_results):
    result = analyze_worker_results(
        [("FIRST.PDF", None, "PlateNeedsOCRException: missing text")]
    )

    assert len(result.failures) == 1
    failure = result.failures[0]
    assert failure.file_name == "FIRST.PDF"
    assert failure.approach.airport == "KAAA"
    assert failure.approach.name == "ILS RWY 01"
    assert failure.exception_message == "PlateNeedsOCRException: missing text"


def test_failure_after_success_uses_failed_approach_labels(analyze_worker_results):
    result = analyze_worker_results(
        [
            ("FIRST.PDF", object(), None),
            ("SECOND.PDF", None, "ValueError: invalid plate"),
        ]
    )

    assert len(result.failures) == 1
    failure = result.failures[0]
    assert failure.file_name == "SECOND.PDF"
    assert failure.approach.airport == "KBBB"
    assert failure.approach.name == "RNAV RWY 02"
    assert failure.exception_message == "ValueError: invalid plate"
