"""
HTTP/HTTPS health check.
Measures: response status code + response time in ms.
A 200-399 status code = healthy.
4xx = client error (misconfigured URL, auth required, etc.)
5xx = server error (service is broken).
None = couldn't connect at all.
"""

import requests
import time

def check_http(url: str, timeout: int = 5) -> tuple[int | None, float | None]:
    """
    Perform a GET request and measure response time.
    Args:
        url — full URL
        timeout — seconds before aborting
    Returns:
        (status_code, response_time_ms)
        (None, None) if the connection failed entirely
        (408, None) if the request timed out
    """
    try:
        start = time.perf_counter()

        browser_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=browser_headers,
            verify=True,  # SSL cert validation
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        return response.status_code, round(elapsed_ms, 1)

    except requests.exceptions.SSLError:
        return 495, None  # SSL handshake failed
    except requests.exceptions.Timeout:
        return 408, 5000  # request timed out
    except requests.exceptions.ConnectionError:
        return 503, None  # couldn't connect at all
    except Exception as e:
        print(f"[HTTP ERROR] {url}: {e}")
        return None, None

"""
Test block for http_monitor
Run this file directly to check HTTP/HTTPS health of a given URL.

if __name__ == "__main__":
    test_url = "https://www.google.com"
    print(f"Checking {test_url}...")
    status, response_time = check_http(test_url)

    if status is None:
        print("Could not connect at all.")
    elif status == 408:
        print("Request timed out.")
    elif status == 495:
        print("SSL handshake failed.")
    elif 200 <= status <= 399:
        print(f"Healthy ({status}), response time: {response_time} ms")
    elif 400 <= status <= 499:
        print(f"Client error ({status})")
    elif 500 <= status <= 599:
        print(f"Server error ({status})")
    else:
        print(f"Unexpected status code: {status}")
"""
