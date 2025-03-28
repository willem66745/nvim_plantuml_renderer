from textual.reactive import var
from textual.worker import Worker
from .monitor import Monitor

from textual.app import ComposeResult, App
from textual.widgets import Footer
from .image import PlantUmlImage


class PlantUmlApp(App[None]):
    CSS = """
        PlantUmlApp {
        }
    """

    BINDINGS = [("q", "quit", "quit")]

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
