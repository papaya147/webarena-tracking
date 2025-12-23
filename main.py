from playwright.sync_api import sync_playwright
import argparse
import tasks
import os
import pathlib
from multiprocessing import Process, Event
import gaze
import time
import json
import threading

WEBEVENT_JS_FILE = "./webevent.js"


# 1. Define helper functions that don't rely on global file handles first
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
        print(f"Login failed: {e}")


# 2. Main Execution Guard
if __name__ == "__main__":
    # --- Setup Logic (moved inside guard) ---
    if not os.path.exists(tasks.TASK_FILE):
        tasks.download()

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--id", type=int, default=0)
    args = parser.parse_args()

    task_detail = tasks.detail(args.id)
    assert task_detail is not None

    print(task_detail["goal"])
    input("Press anything to continue...")

    TASK_DIR = f"./logs/task-{args.id}/"
    INTERACTION_LOGS_FILE = os.path.join(TASK_DIR, "interactions.jsonl")
    TRACE_FILE = os.path.join(TASK_DIR, "trace.zip")
    GAZE_LOGS_FILE = os.path.join(TASK_DIR, "gaze.jsonl")

    pathlib.Path(TASK_DIR).mkdir(parents=True, exist_ok=True)

    # Open file inside main process only
    interaction_file = open(INTERACTION_LOGS_FILE, "w")

    # Define log_event here so it captures 'interaction_file'
    def log_event(batch):
        for data in batch:
            interaction_file.write(json.dumps(data) + "\n")
        interaction_file.flush()

    # Define inject_js here so it captures 'log_event'
    def inject_js(page):
        page.expose_function("log_event_py", log_event)

        with open(WEBEVENT_JS_FILE, "r") as file:
            page.add_init_script(file.read())

        def safe_nav_handler(frame):
            if frame != page.main_frame:
                return
            try:
                if page.is_closed():
                    return
                log_event(
                    [
                        {
                            "type": "navigation",
                            "url": frame.url,
                            "title": page.title(),
                            "timestamp": int(time.time() * 1000),
                        }
                    ]
                )
            except Exception:
                pass

        page._nav_handler = safe_nav_handler
        page.on("framenavigated", safe_nav_handler)

    # --- Start Multiprocessing ---
    stop_sig = Event()
    # The arguments are passed to the separate process safely
    gaze_process = Process(target=gaze.record, args=(GAZE_LOGS_FILE, stop_sig))
    gaze_process.start()

    # --- Start Playwright ---
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1728, "height": 1117})

            context.on("page", inject_js)

            page = context.new_page()

            login(page, task_detail)

            context.tracing.start(screenshots=True, snapshots=True, sources=True)

            print(f"Saving interactions to {INTERACTION_LOGS_FILE}")
            print(f"Saving gaze to {GAZE_LOGS_FILE}")
            print(f"Saving trace to {TRACE_FILE}")

            page.goto(task_detail["domain_detail"]["start_url"])

            print("\n>>> Press Enter here to stop recording and save trace <<< \n")
            stop_recording_event = threading.Event()

            def wait_for_enter():
                try:
                    input()
                except EOFError:
                    pass
                stop_recording_event.set()

            input_thread = threading.Thread(target=wait_for_enter, daemon=True)
            input_thread.start()

            try:
                while not stop_recording_event.is_set():
                    page.wait_for_timeout(100)
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

                context.close()
                browser.close()

    finally:
        # cleanup code runs after playwright closes
        stop_sig.set()
        interaction_file.close()
        gaze_process.join()
        print("Done!")
