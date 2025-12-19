from interaction_logger import InteractionLogger
import time
from playwright.sync_api import sync_playwright, Page
import argparse
import tasks
import os


WEBEVENT_JS_FILE = "./webevent.js"


def log(event_batch):
    for event in event_batch:
        event["server_timestamp"] = int(time.time() * 1000)
        logger.write(event)


def inject_js(page: Page):
    page.expose_function("log_event_py", log)

    with open(WEBEVENT_JS_FILE, "r") as file:
        page.add_init_script(file.read())

    def safe_nav_handler(frame):
        if frame != page.main_frame:
            return
        try:
            if page.is_closed():
                return
            log([{"type": "navigation", "url": frame.url, "title": page.title()}])
        except Exception:
            pass

    page._nav_handler = safe_nav_handler

    page.on("framenavigated", safe_nav_handler)


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


if not os.path.exists(tasks.TASK_FILE):
    tasks.download()

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--id", type=int, default=0)
args = parser.parse_args()


task_detail = tasks.detail(args.id)
assert task_detail is not None

LOG_FILE = f"./logs/task-{args.id}/interactions.jsonl"
TRACE_FILE = f"./logs/task-{args.id}/trace.zip"
logger = InteractionLogger(LOG_FILE)

print(task_detail["goal"])
input("Press anything to continue...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1200, "height": 800})

    context.on("page", inject_js)

    page = context.new_page()

    login(page, task_detail)

    context.tracing.start(screenshots=True, snapshots=True, sources=True)

    print(f"Tracking started. Saving log to {LOG_FILE}")
    print(f"Trace will be saved to {TRACE_FILE}")
    print("Navigate, Scroll, Type, Click.")

    page.goto(task_detail["domain_detail"]["start_url"])

    try:
        input("\n>>> Press Enter here to stop recording and save trace <<< \n")
    except KeyboardInterrupt:
        print("\nInterrupted!")
    finally:
        print("Stopping tracing...")

        if "page" in locals() and hasattr(page, "_nav_handler"):
            try:
                page.remove_listener("framenavigated", page._nav_handler)
            except Exception:
                pass

        try:
            context.tracing.stop(path=TRACE_FILE)
            print(f"Trace saved to {TRACE_FILE}")
        except Exception as e:
            print(f"Error saving trace: {e}")

        try:
            context.close()
            browser.close()
            logger.close()
        except Exception:
            pass

        print("Done.")
