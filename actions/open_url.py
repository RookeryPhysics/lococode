import webbrowser
from lococode.actions.base import BaseTool

class OpenUrlTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "open_url"
        self.description = "Opens a URL in the default web browser. Usage: /url <link>"
        self.pattern = r"/url\s+(.+)"
        self.is_slash = True
        self.intent = "open_url"
        self.arg_description = "URL or website address"

    def execute(self, match, context):
        url = match.group(1).strip()
        # Ensure the URL has a scheme so the browser opens it as a web page
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        print(f"\033[92mOpening: {url}\033[0m")
        webbrowser.open(url)
        return True
