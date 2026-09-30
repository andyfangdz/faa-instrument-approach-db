# Instrument Approach Database

Database of instrument approaches generated from parsing FAA Approach plates.

## Why not use CIFP?

As neat as the free FAA [CIFP](https://www.faa.gov/air_traffic/flight_info/aeronav/digital_products/cifp/download/)
(Coded Instrument Flight Procedures) is, it lack some approaches in the 
`Not_In_CIFP.xlsx` (random internet comment said these are ones which the FAA
has not certified to meet the ARNIC424 standards).

It also lacks some vital information such as the approach minimums. As per an
aeuronautical inquiry, the FAA confirmed the CIFP does not have minimums and
said that they do not offer approach minimums for download in any electronic
format.

Also, as far as I can tell, the CIFP is not a master information source for
approaches either. The master is encoded textually as part of Form 8260-x, e.g
`Form FAA 8260-3 - ILS Standard Instrument Approach Procedure` and are not
available to the public.

CIFP and approach plates are likely derived from this. The Form 8260 is a truly
cursed thing, you can view one
[here](https://github.com/ammaraskar/faa-instrument-approach-db/blob/master/test_data/8260%20ILS%20RWY%2028L%20SFO.pdf).

## Parsing Details

1. Draw just straight lines and rectangles from the PDF. This provides a basic
   tabular structure.

   ![Example of page with lines](test_data/lines.png)

2. Segment the lines/rectangles into different areas based on relative sizes.
   This includes areas such as the missed approach instructions, runway/airport
   information, plan view, communication boxes, profile box, minimums etc.

   ![Example of segmented image](test_data/segmented.png)

3. Extract information from each segmented area such as the minimums.

4. Check for stuff like hold-in-lieu of procedure turns and procedure turn
   barbs.

   ![Example of race track](test_data/race-track.png)

## Development

Use Python 3.12 (see `.python-version`). PyMuPDF 1.24.9 has a prebuilt wheel
for this Python version; Python 3.13 falls back to an incompatible source build.
CI and the publisher use the same version file and require PyMuPDF wheels so
an unsupported interpreter fails promptly instead of compiling MuPDF.

```sh
python -m pip install --only-binary=pymupdf,pymupdfb -r requirements_dev.txt
python -m black . --check
python -m pytest
```

## Publishing

The daily workflow checks the 28-day AIRAC calendar in UTC. On off-cycle days,
**Scrape and publish data** is marked skipped and the schedule job summary says
that no data was published. A green calendar check is not proof of fresh data;
check the latest release tag and its `approaches.json` asset.

After reviewing and merging a publisher repair, a maintainer can use
**Actions → Scrape and Release → Run workflow**, select the repaired branch,
and set **force** to `true` to recover a missed run. This runs the actual FAA
download/extraction and publishes the latest FAA-selected cycle if its release
does not already exist. It can publish data immediately, even off-cycle, so
only dispatch it when release publication is intended. Existing releases and
assets are left untouched. Check the published cycle against the intended FAA
cycle; the manual override does not select a historical cycle.

### Notes:

[Avare](https://github.com/apps4av/avare?tab=readme-ov-file) does geo-referenced
plates. Useful for if we end up showing a map.
