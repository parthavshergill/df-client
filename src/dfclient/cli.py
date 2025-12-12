"""CLI entry point for testing DFHack connectivity."""

import argparse
import sys

from dfclient.client import DFClient


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DFHack RemoteFortressReader client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="DFHack host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="DFHack port (default: 5000)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Test connection
    subparsers.add_parser("test", help="Test connection to DFHack")

    # Get version
    subparsers.add_parser("version", help="Get DFHack/DF version info")

    # Get pause state
    subparsers.add_parser("paused", help="Check if game is paused")

    # Pause game
    subparsers.add_parser("pause", help="Pause the game")

    # Unpause game
    subparsers.add_parser("unpause", help="Unpause the game")

    # Run DFHack command
    run_parser = subparsers.add_parser("run", help="Run a DFHack command")
    run_parser.add_argument("dfhack_command", nargs="+", help="Command to run")

    args = parser.parse_args()

    if not args.command:
        args.command = "test"

    client = DFClient(host=args.host, port=args.port)

    try:
        status = client.connect()

        if not status.connected:
            print(f"Failed to connect: {status.error}")
            print("\nMake sure:")
            print("  1. Dwarf Fortress is running with DFHack")
            print("  2. RemoteFortressReader is enabled:")
            print('     Run "RemoteFortressReader start" in DFHack console')
            return 1

        print(f"Connected to DFHack on {args.host}:{args.port}")

        if args.command == "test":
            print("Connection successful!")
            try:
                version = client.get_version_info()
                print(f"DFHack version: {version.get('dfhack_version', 'unknown')}")
                print(f"DF version: {version.get('df_version', 'unknown')}")
            except Exception as e:
                print(f"(Could not get version info: {e})")

        elif args.command == "version":
            version = client.get_version_info()
            print(f"DFHack version: {version.get('dfhack_version', 'unknown')}")
            print(f"DF version: {version.get('df_version', 'unknown')}")

        elif args.command == "paused":
            is_paused = client.get_pause_state()
            print(f"Game is {'PAUSED' if is_paused else 'RUNNING'}")

        elif args.command == "pause":
            client.pause()
            print("Game paused")

        elif args.command == "unpause":
            client.unpause()
            print("Game unpaused")

        elif args.command == "run":
            cmd = " ".join(args.dfhack_command)
            print(f"Running: {cmd}")
            output = client.run_command(cmd)
            for line in output:
                print(line)

        return 0

    except ConnectionRefusedError:
        print(f"Connection refused on {args.host}:{args.port}")
        print("\nMake sure:")
        print("  1. Dwarf Fortress is running with DFHack")
        print("  2. RemoteFortressReader is enabled")
        return 1

    except Exception as e:
        print(f"Error: {e}")
        return 1

    finally:
        client.disconnect()


if __name__ == "__main__":
    sys.exit(main())
