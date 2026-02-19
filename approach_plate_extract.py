from plate_analyzer import extract_information_from_plate
from plate_analyzer import scrape_faa_dtpp_zip, cifp_analysis
import glob
import os
import re
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

    # Detect CIFP cycle from zip filename in the download folder
    cifp_cycle = ""
    cifp_zips = glob.glob(os.path.join(folder, "CIFP_*.zip"))
    if cifp_zips:
        match = re.search(r"CIFP_(\d+)\.zip", os.path.basename(cifp_zips[0]))
        if match:
            cifp_cycle = match.group(1)

    results = scrape_faa_dtpp_zip.analyze_dtpp_zips(
        folder,
        cifp_file=cifp_file,
        cifp_cycle=cifp_cycle,
    )
    with open("approaches.json", "w") as f:
        f.write(results.model_dump_json())
