# df-client

Play Dwarf Fortress via Claude using DFHack RPC.

## Requirements

- Dwarf Fortress with DFHack installed
- DFHack remote server enabled (RPC on localhost:5000)
- Python 3.11+ with uv

## Setup

```bash
git clone <repo>
cd df-client
uv sync
```

## Usage

```bash
# start daemon (keeps DFHack connection open)
uv run python scripts/daemon.py

# query via netcat
echo '{"cmd":"snapshot"}' | nc localhost 5001
echo '{"cmd":"pause"}' | nc localhost 5001
echo '{"cmd":"play","seconds":30}' | nc localhost 5001
echo '{"cmd":"run","command":"quicksave"}' | nc localhost 5001

# run lua directly
echo '{"cmd":"run","command":"lua print(df.global.pause_state)"}' | nc localhost 5001
```

## Commands

- `snapshot` - get game state (citizens, threats, camera)
- `pause` / `unpause` - control game time
- `play` - unpause for N seconds, return changes
- `run` - execute DFHack console command
- `quit` - stop daemon

## Enable DFHack RPC

Add to `dfhack-config/init/dfhack.init`:
```
enable remote-server
```

Or run in DFHack console:
```
enable remote-server
```
