from notion_client import Client
import os
import json
from datetime import timedelta, datetime, UTC
import logging
import sys
from typing import List

logging.basicConfig(level=logging._nameToLevel[os.environ.get("LOGGING_LEVEL", "INFO")])
_logger = logging.getLogger(__name__)


def extract_datetime_page(page: dict):
    date_time = page["properties"]["Date"]["date"]["start"]
    return datetime.strptime(date_time, "%Y-%m-%d")


def date_time(time_diff: timedelta) -> str:
    date_time = datetime.now() - time_diff
    return date_time.astimezone(UTC).strftime("%Y-%m-%d")


def get_latest_page(pages: List[dict]) -> dict:
    if len(pages) > 1:
        _logger.warning("Got more than one result. Picking the latest one.")
    new_pages = sorted(pages, key=extract_datetime_page, reverse=True)
    return new_pages[0]


def splill_todos(todos: List[dict]) -> dict:
    eligible_todos = []
    for each_todo in todos:
        if each_todo["type"] != "to_do":
            _logger.warning(
                f"Skipping, block:{each_todo['id']} as it's {each_todo['type']} and not to_do type."
            )
            continue
        if (
            each_todo["to_do"]["checked"]
            or each_todo["to_do"]["rich_text"][0]["annotations"]["strikethrough"]
        ):
            _logger.warning(
                f"Skipping, as the block: {each_todo['id']} - {each_todo['to_do']['rich_text'][0]['plain_text']} is either strikedoff or finished."
            )
            continue
        eligible_todos.append(
            {
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": each_todo["to_do"]["rich_text"][0][
                                    "plain_text"
                                ],
                            },
                            "plain_text": "Check pan card",
                        }
                    ],
                    "checked": False,
                    "color": "default",
                },
            }
        )
    return eligible_todos


def main():
    client = Client(auth=os.environ["NOTION_KEY"])
    _logger.info("Registered Notion Client")
    date = date_time(timedelta(days=1))
    children = client.data_sources.query(
        os.environ["NOTION_DATASOURCE_ID"],
        **{
            "filter": {
                "property": "Date",
                "date": {"on_or_after": date},
            }
        },
    )
    _logger.info(
        f"Queried for pages from data source: {os.environ['NOTION_DATASOURCE_ID']}"
    )
    assert children["object"] == "list"
    if len(children["results"]) == 0:
        _logger.error("Cannot find any page results. Exiting")
        sys.exit(1)
    latest_page = get_latest_page(children["results"])
    _logger.info(
        f"Latest page: {latest_page['properties']['Name']['title'][0]['plain_text']} on {latest_page['properties']['Date']['date']['start']} is extracted."
    )
    children = client.blocks.children.list(latest_page["id"])
    _logger.info(
        f"Got todos of page id:{latest_page['id']} and url: {latest_page['url']}"
    )
    assert children["object"] == "list"

    todos = splill_todos(children["results"])

    page = client.pages.create(
        **{
            "parent": {"data_source_id": os.environ["NOTION_DATASOURCE_ID"]},
            "properties": {
                "Name": {"title": [{"text": {"content": "Tasks"}}]},
                "Date": {
                    "type": "date",
                    "date": {
                        "start": datetime.now().strftime("%Y-%m-%d"),
                    },
                },
            },
            "children": todos,
        },
    )
    print(json.dumps(page))


if __name__ == "__main__":
    _logger.info("Started the application")
    main()
