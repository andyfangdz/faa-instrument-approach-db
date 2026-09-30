"""Check the AIRAC calendar without treating unexpected failures as a skip."""

import argparse
from datetime import date, datetime, timezone
import os
from pathlib import Path


AIRAC_EPOCH = date(2024, 1, 25)


def is_airac_date(day: date) -> bool:
    return (day - AIRAC_EPOCH).days % 28 == 0


def check_schedule(day: date, force: bool = False) -> tuple[bool, str]:
    should_run = force or is_airac_date(day)
    if force:
        message = f"Manual override: scraping requested for {day.isoformat()}."
    elif should_run:
        message = f"{day.isoformat()} is an AIRAC effective date; scraping is due."
    else:
        message = (
            f"{day.isoformat()} is not an AIRAC effective date. "
            "The scrape/publish job is skipped; no data was published. "
            "This calendar check does not verify release freshness."
        )
    return should_run, message


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", choices=("true", "false"), default="false")
    args = parser.parse_args()
    day = datetime.now(timezone.utc).date()
    should_run, message = check_schedule(day, force=args.force == "true")
    print(message)
    if "GITHUB_OUTPUT" in os.environ:
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
            output.write(f"should_run={str(should_run).lower()}\n")
    if "GITHUB_STEP_SUMMARY" in os.environ:
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as summary:
            summary.write(f"## AIRAC schedule check\n\n{message}\n")


if __name__ == "__main__":
    main()
