from gradio_client import Client
import json

client = Client("diamond-in/Browser-Use-mcp")

def test():
    print("Testing /get_page_info...")
    res = client.predict(url="https://www.vattenfall.de/", use_persistent=True, api_name="/get_page_info")
    print(res)

    print("\nTesting /click...")
    # Trying to click the cookie consent if it appears.
    # Based on memory: OneTrust cookie consent banner on greencycle.de can be cleared using #onetrust-accept-btn-handler.
    # Vattenfall might have similar.
    res = client.predict(url="https://www.vattenfall.de/", selector="#onetrust-accept-btn-handler", use_persistent=True, api_name="/click")
    print(res)

if __name__ == "__main__":
    test()
