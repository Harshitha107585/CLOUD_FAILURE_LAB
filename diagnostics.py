
import urllib.request
import urllib.error


def check_website(url):
    try:
        request = urllib.request.Request(
            url,
            method="GET"
        )

        with urllib.request.urlopen(
            request,
            timeout=5
        ) as response:
            return {
                "status": "HEALTHY",
                "http_code": response.status,
                "message": "Website responded successfully."
            }

    except urllib.error.HTTPError as error:
        return {
            "status": "ERROR",
            "http_code": error.code,
            "message": f"Website returned HTTP error {error.code}."
        }

    except urllib.error.URLError as error:
        return {
            "status": "UNREACHABLE",
            "http_code": None,
            "message": f"Could not reach website: {error.reason}"
        }

    except TimeoutError:
        return {
            "status": "UNREACHABLE",
            "http_code": None,
            "message": "Connection timed out."
        }

    except Exception as error:
        return {
            "status": "ERROR",
            "http_code": None,
            "message": f"Unexpected error: {error}"
        }
