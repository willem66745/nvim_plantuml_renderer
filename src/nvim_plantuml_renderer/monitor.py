from io import BytesIO
import pynvim
from pynvim.api import Window
from time import sleep
from datetime import datetime, timedelta
from subprocess import Popen, PIPE
from rich.console import Console, ConsoleRenderable
from PIL.Image import open as pil_open
from textual_image.renderable import Image as ConImage
from typing import Literal

type Render = tuple[Literal["error"], str] | tuple[Literal["image"], ConsoleRenderable]


class RenderState:
    def __init__(self):
        self.status: str = "not rendered yet"
        self.image: ConsoleRenderable | None = None

    def handle_render(self, result: Render):
        match result:
            case ("error", error):
                self.status = error
            case ("image", image):
                self.status = ""
                self.image = image

    def handle_no_render(self):
        if self.image is None:
            self.status = "not rendered yet"
        else:
            self.status = "outdated"

    def render(self, con: Console):
        con.clear()
        if len(self.status) > 0:
            con.print(self.status)
        if self.image is not None:
            con.print(self.image)


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
        self.state = RenderState()

    def monitor(self):
        match self.config.connect_params:
            case ("tcp", host, port):
                nvim = pynvim.attach("tcp", address=host, port=port)
            case ("socket", path):
                nvim = pynvim.attach("socket", path=path)

        self.nvim = nvim
        self._wait_poll_nvim()

    def _wait_poll_nvim(self):
        self.con = Console()
        self.con.clear()
        while True:
            sleep_time = self._poll_nvim()
            sleep(sleep_time)

    def _poll_nvim(self) -> float:
        name = self.nvim.current.window.buffer.name

        before = datetime.now()

        r = None

        if name.endswith(".plantuml"):
            r = self._render(self.nvim.current.window.buffer[:])
        elif name.endswith(".md"):
            content = isolate_plantuml(self.nvim.current.window)
            if content:
                r = self._render(content)

        if r is not None:
            self.state.handle_render(r)
        else:
            self.state.handle_no_render()

        self.state.render(self.con)

        duration = datetime.now() - before

        new_timeout = timedelta(seconds=self.config.interval) - duration
        as_float = new_timeout.total_seconds()

        return max(0.0, as_float)

    def _render(self, lines: list[str]) -> Render:
        (out, err) = self._call_plantuml(lines)
        if len(err) > 0:
            return ("error", err.decode("utf-8"))
        elif len(out) > 0:
            pil = pil_open(BytesIO(out))
            con = ConImage(pil)
            return ("image", con)
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
