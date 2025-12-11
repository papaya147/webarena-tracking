import json
import time
from playwright.sync_api import sync_playwright, Page
import argparse


webevent_js_file = "./webevent.js"
log_file = "./logs.jsonl"
task_file = "./tasks.json"


def log_event(event_data):
    event_data["server_timestamp"] = time.time()

    with open(log_file, "a") as f:
        f.write(json.dumps(event_data) + "\n")


def inject_js(page: Page):
    page.expose_function("log_event_py", log_event)

    with open(webevent_js_file, "r") as file:
        page.add_init_script(file.read())

    page.on(
        "framenavigated",
        lambda frame: log_event(
            {"type": "navigation", "url": frame.url, "title": page.title()}
        )
        if frame == page.main_frame
        else None,
    )


def task_details(id: int):
    with open(task_file, "r") as file:
        tasks = json.load(file)

    for task in tasks:
        if task["id"] == id:
            return task

    return "Goal could not be found!"


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

task = task_details(args.id)
assert type(task) is not str, task

print(task["goal"])
input("Press anything to continue...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1640, "height": 1024})

    context.on("page", inject_js)

    page = context.new_page()

    login(page, task)

    print(f"Tracking started. Saving to {log_file}")
    print("Navigate, Scroll, Type, Click. (Press Ctrl+C to stop)")

    page.goto(task["domain_detail"]["start_url"])

    page.wait_for_timeout(99999999)
