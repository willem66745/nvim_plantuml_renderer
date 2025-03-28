from io import BytesIO
import pynvim
from pynvim.api import Window
from subprocess import Popen, PIPE
from PIL.Image import open as pil_open
from PIL import Image as PILImage
from typing import Literal

type Render = tuple[Literal["error"], str] | tuple[Literal["image"], PILImage.Image]
type ConnectParams = tuple[Literal["tcp"], str, int] | tuple[Literal["socket"], str]


def isolate_plantuml(win: Window) -> list[str]:
    """
    search in a nvim window from the cursor position to markdown code fragment
    (```) and or to plantuml markers @startuml/@enduml. When not found, an
    empty array is returned.
    """
    (cur_line, _) = win.cursor
    cur_line -= 1

    first_line = None
    last_line = None

    for line in range(cur_line, -1, -1):
        line_str = win.buffer[line]
        if line_str.strip() == "@startuml":
            first_line = line
            break
        elif "```" in line_str:
            if "```plantuml" in line_str:
                first_line = line + 1
            break

    if first_line is not None:
        for line in range(cur_line, len(win.buffer), 1):
            line_str = win.buffer[line]
            if line_str.strip() == "@enduml":
                last_line = line
                break
            elif "```" in line_str:
                last_line = line - 1
                break

    if first_line is not None and last_line is not None and first_line <= last_line:
        return win.buffer[first_line : last_line + 1]

    return []


class MonitorConfig:
    def __init__(self, executable: str, connect_params: ConnectParams, interval: int):
        self.executable = executable
        self.connect_params = connect_params
        self.interval = interval


class Monitor:
    def __init__(self, config: MonitorConfig):
        self.config = config

    @property
    def interval(self):
        return self.config.interval

    def connect(self):
        match self.config.connect_params:
            case ("tcp", host, port):
                nvim = pynvim.attach("tcp", address=host, port=port)
            case ("socket", path):
                nvim = pynvim.attach("socket", path=path)

        self.nvim = nvim
        # self._wait_poll_nvim()

    def try_render(self) -> Render:
        name = self.nvim.current.window.buffer.name

        r: Render = ("error", "cursor not present at something that can be rendered")

        if name.endswith(".plantuml") or name.endswith(".puml"):
            r = self._render(self.nvim.current.window.buffer[:])
        elif name.endswith(".md"):
            content = isolate_plantuml(self.nvim.current.window)
            if content:
                r = self._render(content)

        return r

    def _render(self, lines: list[str]) -> Render:
        (out, err) = self._call_plantuml(lines)
        if len(err) > 0:
            return ("error", err.decode("utf-8"))
        elif len(out) > 0:
            pil = pil_open(BytesIO(out))
            return ("image", pil)
        else:
            return ("error", "plantuml didn't return anything")

    def _call_plantuml(self, lines: list[str]) -> tuple[bytes, bytes]:
        content = "\n".join(lines).encode("utf-8")
        p = Popen(
            [self.config.executable, "-tpng", "-p"],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
        )
        return p.communicate(input=content)
