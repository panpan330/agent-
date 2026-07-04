import requests


def main() -> None:
    response = requests.get("https://httpbin.org/get", timeout=10)
    print("status:", response.status_code)
    print("content-type:", response.headers.get("content-type"))

    data = response.json()
    print("url:", data["url"])
    print("origin:", data["origin"])


if __name__ == "__main__":
    main()
