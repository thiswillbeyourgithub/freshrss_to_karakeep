"""
freshrss_to_karakeep.py - Transfer saved items from FreshRSS to Karakeep
"""

import os
import re
import sys
from typing import List, Optional

import click
from loguru import logger
from freshrss_api import FreshRSSAPI
from karakeep_python_api import KarakeepAPI, datatypes, APIError, AuthenticationError

VERSION: str = "1.2.0"


# Configure logging
logger.remove()  # Remove default handler
logger.add("./log.txt", level="DEBUG", rotation="10 MB")  # File output always at DEBUG level


@click.command()
@click.option(
    "--needed-regex",
    default=".*",
    help="Only include items with URLs matching this regex",
)
@click.option(
    "--ignore-regex", default="", help="Exclude items with URLs matching this regex"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Don't actually transfer items, just show what would be transferred",
)
@click.option(
    "--unsave-freshrss/--no-unsave-freshrss",
    default=True,
    help="Whether to unsave items from FreshRSS after transfer (default: True)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed log messages in console output",
)
@click.option(
    "--mark-as-read/--no-mark-as-read",
    default=True,
    help="Whether to mark items as read in FreshRSS after transfer (default: True, only if unsaved)",
)
def main(needed_regex: str, ignore_regex: str, dry_run: bool, unsave_freshrss: bool, verbose: bool, mark_as_read: bool):
    # Configure console logging based on verbose flag
    console_level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stderr, level=console_level)  # Console output
    """
    Transfer saved items from FreshRSS to Karakeep.

    This script fetches saved items from FreshRSS, filters them based on regex patterns,
    adds them as bookmarks to Karakeep with the tag 'freshrss', and then optionally 
    unsaves them from FreshRSS after successful transfer (controlled by --unsave-freshrss flag).
    If items are unsaved, they can also be marked as read (controlled by --mark-as-read flag).
    """
    logger.info("Starting FreshRSS to Karakeep transfer")

    # Compile regex patterns
    needed_pattern = re.compile(needed_regex)
    ignore_pattern = re.compile(ignore_regex) if ignore_regex else None

    # Initialize FreshRSS API client
    freshrss_client = FreshRSSAPI(verbose=True)
    logger.info("Successfully connected to FreshRSS API")

    # Initialize Karakeep API client
    karakeep_client = KarakeepAPI()

    if not karakeep_client:
        logger.error("Failed to initialize Karakeep client. Exiting.")
        sys.exit(1)
    logger.info("Successfully connected to Karakeep API")

    # Get saved items from FreshRSS
    saved_items = freshrss_client.get_saved()
    logger.info(f"Retrieved {len(saved_items)} saved items from FreshRSS")

    # Filter items based on regex patterns
    filtered_items = []
    for item in saved_items:
        if not needed_pattern.search(item.url):
            logger.debug(f"Skipping item (doesn't match needed regex): {item.url}")
            continue

        if ignore_pattern and ignore_pattern.search(item.url):
            logger.debug(f"Skipping item (matches ignore regex): {item.url}")
            continue

        filtered_items.append(item)

    logger.info(f"After filtering, {len(filtered_items)} items remain for processing")

    if dry_run:
        logger.info("DRY RUN MODE: Would transfer these items:")
        for item in filtered_items:
            logger.info(f"- {item.title} ({item.url})")
        return

    # Process each filtered item
    for item in filtered_items:
        try:
            # Create bookmark in Karakeep
            logger.info(f"Creating bookmark for: {item.title}")
            bookmark = karakeep_client.create_a_new_bookmark(
                type="link", url=item.url, title=item.title
            )

            if not bookmark or not bookmark.id:
                logger.error(f"Failed to create bookmark for {item.url}")
                continue

            logger.info(f"Created bookmark with ID: {bookmark.id}")

            # Add 'freshrss' tag to the bookmark
            logger.info(f"Adding 'freshrss' tag to bookmark {bookmark.id}")
            tag_payload = {"tags": [{"tagName": "freshrss"}]}

            attach_response = karakeep_client.attach_tags_to_a_bookmark(
                bookmark_id=bookmark.id, tags_data=tag_payload
            )

            if "attached" in attach_response and len(attach_response["attached"]) > 0:
                tag_id = attach_response["attached"][0]
                logger.info(
                    f"Tag 'freshrss' (ID: {tag_id}) attached to bookmark {bookmark.id}"
                )
            else:
                logger.warning(f"Failed to attach tag to bookmark {bookmark.id}")

            # Unsave item from FreshRSS if specified
            if unsave_freshrss:
                logger.info(f"Unsaving item from FreshRSS: {item.title}")
                resp = freshrss_client.set_mark(as_="unsaved", id=item.id)
                logger.debug(f"Unsave response: {resp}")
                logger.info(f"Successfully unsaved item from FreshRSS: {item.title}")

                if mark_as_read:
                    logger.info(f"Marking item as read in FreshRSS: {item.title}")
                    read_resp = freshrss_client.set_mark(as_="read", id=item.id)
                    logger.debug(f"Mark as read response: {read_resp}")
                    logger.info(f"Successfully marked item as read in FreshRSS: {item.title}")
            else:
                logger.info(f"Keeping item saved in FreshRSS: {item.title}")

        except (APIError, AuthenticationError) as e:
            logger.error(f"Error processing item {item.url}: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error processing item {item.url}: {e}")

    logger.info("FreshRSS to Karakeep transfer completed")


if __name__ == "__main__":
    main()
