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
        self.status: str = "not render yet"
        self.image: ConsoleRenderable | None = None

    def handle_render(self, result: Render):
        outcome = result[0]
        if outcome == "error":
            error = result[1]
            if type(error) is str:
                self.status = error
        elif outcome == "image":
            image = result[1]
            if isinstance(image, ConsoleRenderable):
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


def monitor(connect_params: ConnectParams, interval: int):
    match connect_params:
        case ("tcp", host, port):
            nvim = pynvim.attach("tcp", address=host, port=port)
        case ("socket", path):
            nvim = pynvim.attach("socket", path=path)

    wait_poll_nvim(nvim, interval)


def wait_poll_nvim(nvim: pynvim.Nvim, interval: int):
    state = RenderState()
    con = Console()
    con.clear()
    while True:
        sleep_time = poll_nvim(nvim, con, state, interval)
        sleep(sleep_time)


def poll_nvim(
    nvim: pynvim.Nvim, con: Console, state: RenderState, interval: int
) -> float:
    name = nvim.current.window.buffer.name

    before = datetime.now()

    r = None

    if name.endswith(".plantuml"):
        r = render(nvim.current.window.buffer[:])
    elif name.endswith(".md"):
        content = isolate_plantuml(nvim.current.window)
        if content:
            r = render(content)

    if r is not None:
        state.handle_render(r)
    else:
        state.handle_no_render()

    state.render(con)

    duration = datetime.now() - before

    new_timeout = timedelta(seconds=interval) - duration
    as_float = new_timeout.total_seconds()

    return max(0.0, as_float)


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


def render(lines: list[str]) -> Render:
    (out, err) = call_plantuml(lines)
    if len(err) > 0:
        return ("error", err.decode("utf-8"))
    elif len(out) > 0:
        pil = pil_open(BytesIO(out))
        con = ConImage(pil)
        return ("image", con)
    else:
        return ("error", "plantuml didn't return anything")


def call_plantuml(lines: list[str]) -> tuple[bytes, bytes]:
    content = "\n".join(lines).encode("utf-8")
    p = Popen(["plantuml", "-tpng", "-p"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    return p.communicate(input=content)
