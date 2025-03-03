import argparse
import shutil
from .monitor import monitor
from subprocess import Popen, PIPE


def _plantuml_is_ok(plantuml: str) -> bool:
    run = Popen([plantuml, "-version"], stdout=PIPE, stderr=PIPE)

    (out, err) = run.communicate()

    plantuml_is_ok = b"Installation seems OK" in out and b"File generation OK" in out

    return run.returncode == 0 and len(err) == 0 and plantuml_is_ok


def main():
    parser = argparse.ArgumentParser(description="Script to connect to a server.")
    parser.add_argument(
        "--plantuml", help="Plantuml executable location (by default lookup in PATH)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Hostname to connect to (default: localhost)",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--port", type=int, help="Port number to connect to")
    group.add_argument("--path", type=str, help="Path to socket")

    parser.add_argument(
        "--interval", type=int, default=5, help="Monitor interval in seconds"
    )

    args = parser.parse_args()

    host = args.host
    port = args.port
    path = args.path
    interval = args.interval
    plantuml = args.plantuml
    if plantuml is None:
        plantuml = shutil.which("plantuml")

    if plantuml is None or not _plantuml_is_ok(plantuml):
        parser.error("Plantuml executable not found")

    if path is not None:
        connect_params = ("socket", path)
    else:
        connect_params = ("tcp", host, port)

    monitor(plantuml, connect_params, interval)
