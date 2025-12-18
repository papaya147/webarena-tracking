# from event_logger_old import EventLogger
from interaction_logger import InteractionLogger
import json
import time
from playwright.sync_api import sync_playwright, Page
import argparse
import tasks


WEBEVENT_JS_FILE = "./webevent.js"
LOG_FILE = "./logs.jsonl"

logger = InteractionLogger(LOG_FILE)


def log(event_batch):
    for event in event_batch:
        logger.write(event)


def inject_js(page: Page):
    page.expose_function("log_event_py", log)

    with open(WEBEVENT_JS_FILE, "r") as file:
        page.add_init_script(file.read())

    page.on(
        "framenavigated",
        lambda frame: log(
            [{"type": "navigation", "url": frame.url, "title": page.title()}]
        )
        if frame == page.main_frame
        else None,
    )


def login(page, task):
    if task["domain_detail"]["domain"] == "__MAP__":
        return

    domain_detail = task["domain_detail"]

    try:
        page.goto(domain_detail["login_url"])
        page.wait_for_selector(domain_detail["username_field"], timeout=5000)
        page.fill(domain_detail["username_field"], domain_detail["username"])
        page.fill(domain_detail["password_field"], domain_detail["password"])

        page.click(domain_detail["login_button"])
        page.wait_for_load_state("networkidle")
    except Exception as e:
        print(e)


parser = argparse.ArgumentParser()
parser.add_argument("-i", "--id", type=int, default=0)
args = parser.parse_args()

task_detail = tasks.detail(args.id)
assert task_detail is not None

print(task_detail["goal"])
input("Press anything to continue...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1200, "height": 800})

    context.on("page", inject_js)

    page = context.new_page()

    login(page, task_detail)

    print(f"Tracking started. Saving to {LOG_FILE}")
    print("Navigate, Scroll, Type, Click. (Press Ctrl+C to stop)")

    page.goto(task_detail["domain_detail"]["start_url"])

    page.wait_for_timeout(99999999)

logger.close()
