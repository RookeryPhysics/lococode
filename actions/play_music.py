import webbrowser
from lococode.actions.base import BaseTool

class PlayMusicTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "music"
        self.description = "Play music by opening a specific YouTube URL. Usage: /music"
        self.pattern = r"^/music\b.*$"
        self.is_slash = True
        self.intent = "music"
        self.arg_description = None

    def execute(self, match, context):
        url = "https://www.youtube.com/watch?v=U5by55dkYlI&list=LL&index=6"
        print(f"\033[36mPlaying music: {url}\033[0m")
        webbrowser.open(url)
        return True
