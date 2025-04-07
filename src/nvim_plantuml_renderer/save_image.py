from PIL import Image as PILImage

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.screen import Screen
from textual.containers import Container
from textual.validation import ValidationResult, Validator
from textual.widgets import DirectoryTree, Footer, Input

from datetime import datetime
from typing import Iterable
from pathlib import Path


class Filename(Validator):
    def validate(self, value: str) -> ValidationResult:
        if "/" not in value and "\\" not in value and "." not in value:
            return self.success()
        else:
            return self.failure()


class OnlyDirectoryTree(DirectoryTree):
    BINDINGS = [
        Binding("h", "parent", "parent", show=False),
        Binding("left", "parent", "parent", show=False),
        Binding("l", "select_cursor", "select", show=False),
        Binding("right", "select_cursor", "select", show=False),
        Binding("j", "cursor_down", "down", show=False),
        Binding("k", "cursor_up", "up", show=False),
    ]

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path.is_dir()]

    def action_parent(self):
        item = Path(self.path)
        self.path = item.parent

    def action_select_cursor(self):
        if self.cursor_node is not None and self.cursor_node.data is not None:
            self.path = self.cursor_node.data.path


class SaveImageContainer(Container):
    DEFAULT_CSS = """
    SaveImageContainer {
        border: round gray;
    }
    """

    def compose(self) -> ComposeResult:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        path = Path("~/Pictures/").expanduser()
        if not path.is_dir() or not path.exists():
            path = Path("~").expanduser()

        yield Input(f"plantuml_{timestamp}", validators=[Filename()])
        yield OnlyDirectoryTree(path)


class SaveImageScreen(Screen[Path]):
    class ImageSaved(Message):
        pass

    BINDINGS = [("q", "quit", "quit")]

    def __init__(self, *args, image: PILImage.Image, **kwargs):
        self._image = image
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield SaveImageContainer()
        yield Footer(show_command_palette=False)

    def action_quit(self):
        self.app.exit()

    @on(Input.Submitted)
    def write_file(self, event: Input.Submitted):
        path = (
            Path(self.query_one(OnlyDirectoryTree).path)
            .joinpath(event.value)
            .with_suffix(".png")
        )
        self._image.save(path)
        self.post_message(self.ImageSaved())
