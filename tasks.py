import requests
import json

domain_details = [
    {
        "domain": "__SHOPPING_ADMIN__",
        "start_url": "http://localhost:8083/admin",
        "login_url": "http://localhost:8083/admin",
        "username_field": "#username",
        "username": "admin",
        "password_field": "#login",
        "password": "admin1234",
        "login_button": ".action-login",
    },
    {
        "domain": "__SHOPPING__",
        "start_url": "http://localhost:8082",
        "login_url": "http://localhost:8082/customer/account/login/",
        "username_field": "#email",
        "username": "emma.lopez@gmail.com",
        "password_field": "#pass",
        "password": "Password.123",
        "login_button": "#send2",
    },
    {
        "domain": "__REDDIT__",
        "start_url": "http://localhost:8080",
        "login_url": "http://localhost:8080/login",
        "username_field": "#login-username",
        "username": "MarvelsGrantMan136",
        "password_field": "#login-password",
        "password": "test1234",
        "login_button": ".button",
    },
    {
        "domain": "__GITLAB__",
        "start_url": "http://localhost:9001",
        "login_url": "http://localhost:9001/users/sign_in",
        "username_field": "#user_login",
        "username": "byteblaze",
        "password_field": "#user_password",
        "password": "hello1234",
        "login_button": "[data-qa-selector='sign_in_button']",
    },
    {
        "domain": "__MAP__",
        "start_url": "http://localhost:443",
    },
]


def domain_detail(url):
    for domain_detail in domain_details:
        if url == domain_detail["domain"]:
            return domain_detail


TASK_URL = "https://raw.githubusercontent.com/web-arena-x/webarena/refs/heads/main/config_files/test.raw.json"
TASK_FILE = "./tasks.json"


def download():
    print(f"Downloading tasks from {TASK_URL}...")

    response = requests.get(TASK_URL)
    response.raise_for_status()
    data = response.json()

    extracted_tasks = [
        {
            "id": task["task_id"],
            "goal": task["intent"],
            "domain_detail": domain_detail(task["start_url"]),
        }
        for task in data
    ]

    with open(TASK_FILE, "w") as f:
        json.dump(extracted_tasks, f, indent=2)

    print(f"Success! Dumped {len(extracted_tasks)} tasks to '{TASK_FILE}'.")


def detail(id: int):
    with open(TASK_FILE, "r") as file:
        tasks = json.load(file)

    for task in tasks:
        if task["id"] == id:
            return task

    print("Goal could not be found.")
    return None
