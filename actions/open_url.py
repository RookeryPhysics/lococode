import re
import webbrowser
from lococode.actions.base import BaseTool

class OpenUrlTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "open_url"
        self.description = "Open a given URL in the default web browser. Usage: /url <url>"
        self.pattern = r"^/url\s+(.+)$"
        self.is_slash = True
        self.intent = "open_url"
        self.arg_description = "URL to open"

    def execute(self, match, context):
        url = match.group(1)
        if not url:
            print("\033[31mPlease provide a URL. Usage: /url <url>\033[0m")
            return True
            
        url = url.strip()
        if not url.startswith(('http://', 'https://', 'file://')):
            url = 'https://' + url
            
        print(f"\033[36mOpening URL: {url}\033[0m")
        webbrowser.open(url)
        return True
