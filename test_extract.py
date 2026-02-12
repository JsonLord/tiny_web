from gradio_client import Client
client = Client("diamond-in/Browser-Use-mcp")
res = client.predict(url="https://www.vattenfall.de/", selector="body", use_persistent=True, api_name="/browse_and_extract")
print(res)
