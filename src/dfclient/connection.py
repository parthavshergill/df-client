"""Low-level TCP connection and RPC protocol for DFHack."""

import socket
import struct
from dataclasses import dataclass
from typing import Callable

from dfclient.models import ConnectionStatus, RPCError


# DFHack RPC Protocol Constants
DFHACK_MAGIC_REQUEST = b"DFHack?\n"
DFHACK_MAGIC_RESPONSE = b"DFHack!\n"
DFHACK_VERSION = 1

# RPC result codes
RPC_REPLY_RESULT = -1
RPC_REPLY_FAIL = -2
RPC_REPLY_TEXT = -3
RPC_REQUEST_QUIT = -4


def _decode_text_message(data: bytes) -> str:
    """Decode a TEXT reply which is protobuf-wrapped.

    Format: field 1 (CoreTextNotification) → field 1 (text string)
    """
    if not data:
        return ""

    try:
        # Parse outer message
        pos = 0
        while pos < len(data):
            # Read tag
            tag = data[pos]
            pos += 1
            field_num = tag >> 3
            wire_type = tag & 0x7

            if wire_type == 2:  # length-delimited
                # Read length (varint)
                length = 0
                shift = 0
                while pos < len(data):
                    byte = data[pos]
                    pos += 1
                    length |= (byte & 0x7F) << shift
                    if not (byte & 0x80):
                        break
                    shift += 7

                if field_num == 1:
                    # This is the inner message, parse it
                    inner = data[pos:pos + length]
                    # Parse inner to get field 1 (the actual text)
                    ipos = 0
                    while ipos < len(inner):
                        itag = inner[ipos]
                        ipos += 1
                        ifield = itag >> 3
                        iwire = itag & 0x7

                        if iwire == 2:
                            ilen = 0
                            ishift = 0
                            while ipos < len(inner):
                                byte = inner[ipos]
                                ipos += 1
                                ilen |= (byte & 0x7F) << ishift
                                if not (byte & 0x80):
                                    break
                                ishift += 7

                            if ifield == 1:
                                return inner[ipos:ipos + ilen].decode("utf-8", errors="replace")
                            ipos += ilen
                        else:
                            break
                pos += length
            else:
                break
    except Exception:
        pass

    # Fallback: try direct decode
    return data.decode("utf-8", errors="replace")


@dataclass
class RPCMessage:
    """A raw RPC message."""
    id: int  # Method ID or result code
    data: bytes


class DFHackConnection:
    """Low-level connection to DFHack RPC server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5000, timeout: float = 30.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket: socket.socket | None = None
        self._connected = False
        self._dfhack_version: str = ""

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self) -> ConnectionStatus:
        """Connect to DFHack and perform handshake."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout)
            self._socket.connect((self.host, self.port))

            # Send handshake
            self._socket.sendall(DFHACK_MAGIC_REQUEST)
            self._socket.sendall(struct.pack("<I", DFHACK_VERSION))

            # Read response
            response_magic = self._recv_exact(len(DFHACK_MAGIC_RESPONSE))
            if response_magic != DFHACK_MAGIC_RESPONSE:
                raise ConnectionError(f"Invalid magic: {response_magic!r}")

            version_data = self._recv_exact(4)
            server_version = struct.unpack("<I", version_data)[0]
            self._dfhack_version = str(server_version)

            self._connected = True
            return ConnectionStatus(
                connected=True,
                dfhack_version=self._dfhack_version,
            )

        except Exception as e:
            self._connected = False
            return ConnectionStatus(
                connected=False,
                error=str(e),
            )

    def disconnect(self) -> None:
        """Close the connection."""
        if self._socket:
            try:
                # Send quit request
                self._send_message(RPCMessage(id=RPC_REQUEST_QUIT, data=b""))
            except Exception:
                pass
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
        self._connected = False

    def _recv_exact(self, n: int) -> bytes:
        """Receive exactly n bytes."""
        if not self._socket:
            raise ConnectionError("Not connected")

        data = b""
        while len(data) < n:
            chunk = self._socket.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data

    def _send_message(self, msg: RPCMessage) -> None:
        """Send an RPC message."""
        if not self._socket:
            raise ConnectionError("Not connected")

        # Header: method_id (2 bytes signed) + padding (2 bytes) + size (4 bytes)
        header = struct.pack("<hxxI", msg.id, len(msg.data))
        self._socket.sendall(header)
        if msg.data:
            self._socket.sendall(msg.data)

    def _recv_message(self) -> RPCMessage:
        """Receive an RPC message."""
        # Read header
        header = self._recv_exact(8)
        msg_id, size = struct.unpack("<hxxI", header)

        # Read data
        data = self._recv_exact(size) if size > 0 else b""

        return RPCMessage(id=msg_id, data=data)

    def call(
        self,
        method_id: int,
        request_data: bytes = b"",
        text_callback: Callable[[str], None] | None = None,
    ) -> bytes:
        """
        Call an RPC method and return the response data.

        Args:
            method_id: The method ID to call
            request_data: Serialized protobuf request
            text_callback: Optional callback for text messages (like console output)

        Returns:
            The response data bytes

        Raises:
            RPCError: If the call fails
        """
        if not self._connected:
            raise ConnectionError("Not connected")

        # Send request
        self._send_message(RPCMessage(id=method_id, data=request_data))

        # Process responses until we get the result
        while True:
            response = self._recv_message()

            if response.id == RPC_REPLY_TEXT:
                # Text message (console output) - protobuf wrapped
                if text_callback and response.data:
                    text = _decode_text_message(response.data)
                    if text:
                        text_callback(text)
                continue

            elif response.id == RPC_REPLY_FAIL:
                # Error response
                error_msg = response.data.decode("utf-8", errors="replace") if response.data else "Unknown error"
                raise Exception(f"RPC failed: {error_msg}")

            elif response.id == RPC_REPLY_RESULT:
                # Success
                return response.data

            else:
                # Unexpected response type
                raise Exception(f"Unexpected response type: {response.id}")

    def __enter__(self) -> "DFHackConnection":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
