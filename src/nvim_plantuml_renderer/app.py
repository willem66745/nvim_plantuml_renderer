from textual.app import ComposeResult, App
from textual.reactive import var
from textual.widgets import Footer
from textual.screen import Screen
from textual.worker import Worker

from .monitor import Monitor
from .image import PlantUmlImage
from .save_image import SaveImageScreen


class PlantUmlScreen(Screen):
    CSS = """
        PlantUmlApp {
        }
    """

    BINDINGS = [("q", "quit", "quit"), ("w", "write_image", "write image")]

    worker: var[Worker | None] = var(None)

    def __init__(self, *args, monitor: Monitor, **kwargs):
        self._monitor = monitor
        super().__init__(*args, **kwargs)

    def on_mount(self):
        self.set_interval(self._monitor.interval, self.start_worker)
        self.start_worker()

    def compose(self) -> ComposeResult:
        yield PlantUmlImage()
        yield Footer(show_command_palette=False)

    def start_worker(self):
        def start_for_real():
            self.worker = self.run_worker(self.render_worker, thread=True)

        if self.worker is None:
            start_for_real()
        else:
            if not self.worker.is_running:
                start_for_real()

    def render_worker(self):
        r = self._monitor.try_render()
        match r:
            case ("error", text):
                self.query_one(PlantUmlImage).status = text
            case ("image", image):
                self.query_one(PlantUmlImage).status = ""
                self.query_one(PlantUmlImage).image = image
            case ("no_change", _):
                pass

    def action_write_image(self):
        image = self.query_one(PlantUmlImage).image
        if image is not None:
            # image.save("bla.png")
            self.app.switch_screen(SaveImageScreen(image=image))
            pass
        else:
            self.notify("no image rendered yet by Plantuml")

    def action_quit(self):
        self.app.exit()


class PlantUmlApp(App[None]):
    def __init__(self, *args, monitor: Monitor, **kwargs):
        self._monitor = monitor
        super().__init__(*args, **kwargs)

    def on_mount(self):
        self.push_screen(PlantUmlScreen(monitor=self._monitor))

    def on_save_image_screen_image_saved(self, _: SaveImageScreen.ImageSaved):
        self._monitor.refresh()
        self.switch_screen(PlantUmlScreen(monitor=self._monitor))
