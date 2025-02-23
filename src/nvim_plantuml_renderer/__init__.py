import argparse
from .monitor import monitor


def main():
    parser = argparse.ArgumentParser(description="Script to connect to a server.")
    parser.add_argument(
        "--host",
        default="localhost",
        help="Hostname to connect to (default: localhost)",
    )
    parser.add_argument(
        "--port", required=True, type=int, help="Port number to connect to"
    )
    parser.add_argument(
        "--interval", type=int, default=5, help="Monitor interval in seconds"
    )

    args = parser.parse_args()

    host = args.host
    port = args.port
    interval = args.interval

    monitor(host, port, interval)
