import argparse
from .monitor import monitor


def main():
    parser = argparse.ArgumentParser(description="Script to connect to a server.")
    parser.add_argument(
        "--host",
        default="localhost",
        help="Hostname to connect to (default: localhost)",
    )
    parser.add_argument("--port", type=int, help="Port number to connect to")
    parser.add_argument("--path", type=str, help="Path to socket")
    parser.add_argument(
        "--interval", type=int, default=5, help="Monitor interval in seconds"
    )

    args = parser.parse_args()

    host = args.host
    port = args.port
    path = args.path
    interval = args.interval

    if path is not None:
        connect_params = ("socket", path)
    else:
        connect_params = ("tcp", host, port)

    monitor(connect_params, interval)
