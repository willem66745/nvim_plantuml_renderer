from PIL import Image as PILImage

from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Label

from textual_image.widget import Image


class PlantUmlImage(Container):
    image: reactive[PILImage.Image | None] = reactive(None)
    status: reactive[str] = reactive("initializing...")

    DEFAULT_CSS = """
    PlantUmlImage {
        border: round gray;
        align: center top;

        #image_container {
            align: center middle;
            width: 100%;
        }

        Image {
            width: auto;
            height: auto;
        }

        #status_container {
            width: 100%;
            height: auto;
        }
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="image_container"):
            yield Image()
        with Container(id="status_container"):
            yield Label()

    def watch_status(self, _, new_status):
        self.query_one(Label).update(new_status)

    def watch_image(self, _, new_image):
        self.query_one(Image).image = new_image
