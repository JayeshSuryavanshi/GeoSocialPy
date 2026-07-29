"""Command-line entry point for GeoSocialPy.

Installed as the ``geosocialpy`` console script (see ``[project.scripts]`` in
``pyproject.toml``). Fetches geotagged tweets within a radius and writes them to
a newline-delimited JSON file.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Sequence

from geosocialpy.data_fetcher import TwitterDataFetcher


def _load_env() -> None:
    """Load a local ``.env`` if python-dotenv (the ``example`` extra) is present."""
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return
    load_dotenv()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="geosocialpy",
        description="Fetch geotagged tweets within a radius via the X API v2.",
    )
    parser.add_argument(
        "--geocode",
        default="37.7749,-122.4194,10mi",
        help='"latitude,longitude,radius", e.g. "37.7749,-122.4194,10mi".',
    )
    parser.add_argument(
        "--count", type=int, default=100, help="Maximum number of tweets to fetch."
    )
    parser.add_argument(
        "--output", default="tweets.json", help="Path to write newline-delimited JSON."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Log fetch errors to stderr."
    )
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    _load_env()
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        raise SystemExit(
            "TWITTER_BEARER_TOKEN is not set. Add it to your environment or a "
            ".env file. To read a .env file install the example extra: "
            'pip install "geosocialpy[example]".'
        )

    fetcher = TwitterDataFetcher(bearer_token=bearer_token)
    tweets = fetcher.fetch_tweets(args.geocode, count=args.count)
    if tweets is None:
        raise SystemExit("Failed to fetch tweets (run with --verbose for details).")

    fetcher.save_tweets_to_file(tweets, args.output)
    message = f"Saved {len(tweets)} tweets to {args.output}"
    if fetcher.places:
        places_path = f"{args.output}.places.json"
        fetcher.save_places_to_file(places_path)
        message += f" and {len(fetcher.places)} place bboxes to {places_path}"
    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
