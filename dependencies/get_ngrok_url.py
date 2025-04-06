import requests

def get_ngrok_url(GIST_ID):
    GIST_URL = f"https://api.github.com/gists/{GIST_ID}"
    try:
        response = requests.get(GIST_URL).json()
        ngrok_url = response["files"]["ngrok_url.txt"]["content"]
        return ngrok_url
    except Exception as e:
        print(f"Failed to fetch ngrok URL: {e}")
        return None