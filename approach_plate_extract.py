from plate_analyzer import extract_information_from_plate
from plate_analyzer import scrape_faa_dtpp_zip, cifp_analysis
import sys


if __name__ == "__main__":
    # extract_information_from_plate("../../Downloads/06065R8.PDF", debug=True)
    # extract_information_from_plate("test_data/05222VT15.pdf", debug=True)
    # extract_information_from_plate("test_data/05889LDE.pdf", debug=True)

    # cifp_analysis.analyze_cifp_file("../../Downloads/faa_dttp/FAACIFP18")

    if len(sys.argv) > 1:
        folder = sys.argv[1]
        cifp_file = sys.argv[2]
    else:
        folder = "../../Downloads/faa_dttp/250320"
        cifp_file = "../../Downloads/faa_dttp/250320/FAACIFP18"

    results = scrape_faa_dtpp_zip.analyze_dtpp_zips(
        folder,
        cifp_file=cifp_file,
    )
    with open("approaches.json", "w") as f:
        f.write(results.model_dump_json())
