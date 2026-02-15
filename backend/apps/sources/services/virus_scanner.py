"""
Virus scanning service for uploaded files.

This module provides virus scanning via ClamAV daemon.
Supports both local Unix socket and TCP connections.
"""

import logging
import socket
import struct
import time
from dataclasses import dataclass
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


# ClamAV configuration from settings
CLAMAV_HOST = getattr(settings, 'CLAMAV_HOST', 'localhost')
CLAMAV_PORT = getattr(settings, 'CLAMAV_PORT', 3310)
CLAMAV_SOCKET_PATH = getattr(settings, 'CLAMAV_SOCKET_PATH', '/var/run/clamav/clamd.ctl')
CLAMAV_USE_SOCKET = getattr(settings, 'CLAMAV_USE_SOCKET', False)
CLAMAV_TIMEOUT = getattr(settings, 'CLAMAV_TIMEOUT', 60)  # seconds
CLAMAV_CHUNK_SIZE = 2048  # bytes per chunk for INSTREAM


@dataclass
class VirusScanResult:
    """Result of a virus scan operation."""
    is_clean: bool
    threat_name: Optional[str]
    scan_time_ms: int
    error: Optional[str] = None


class VirusScannerError(Exception):
    """Exception raised when virus scanning fails."""
    pass


class VirusScanner:
    """
    Virus scanner service using ClamAV daemon.

    Supports two connection modes:
    - TCP: Connect to clamd on host:port (default: localhost:3310)
    - Unix socket: Connect via socket file (e.g., /var/run/clamav/clamd.ctl)

    Configuration via Django settings:
    - CLAMAV_ENABLED: Enable/disable virus scanning (default: False)
    - CLAMAV_HOST: ClamAV daemon host (default: localhost)
    - CLAMAV_PORT: ClamAV daemon port (default: 3310)
    - CLAMAV_SOCKET_PATH: Unix socket path (default: /var/run/clamav/clamd.ctl)
    - CLAMAV_USE_SOCKET: Use Unix socket instead of TCP (default: False)
    - CLAMAV_TIMEOUT: Connection timeout in seconds (default: 60)
    """

    def __init__(self):
        self.enabled = getattr(settings, 'CLAMAV_ENABLED', False)

    def _get_socket(self) -> socket.socket:
        """
        Create and connect a socket to the ClamAV daemon.

        Returns:
            Connected socket instance

        Raises:
            VirusScannerError: If connection fails
        """
        try:
            if CLAMAV_USE_SOCKET:
                # Unix socket connection
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(CLAMAV_TIMEOUT)
                sock.connect(CLAMAV_SOCKET_PATH)
                logger.debug(f"Connected to ClamAV via Unix socket: {CLAMAV_SOCKET_PATH}")
            else:
                # TCP connection
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(CLAMAV_TIMEOUT)
                sock.connect((CLAMAV_HOST, CLAMAV_PORT))
                logger.debug(f"Connected to ClamAV via TCP: {CLAMAV_HOST}:{CLAMAV_PORT}")

            return sock

        except socket.error as e:
            raise VirusScannerError(f"Failed to connect to ClamAV daemon: {e}")

    def _send_command(self, sock: socket.socket, command: str) -> str:
        """
        Send a command to ClamAV and read the response.

        Args:
            sock: Connected socket
            command: Command to send (e.g., "PING", "VERSION")

        Returns:
            Response string from ClamAV
        """
        sock.sendall(f"n{command}\n".encode())
        response = sock.recv(4096).decode().strip()
        return response

    def ping(self) -> bool:
        """
        Check if ClamAV daemon is responding.

        Returns:
            True if daemon responds with PONG, False otherwise
        """
        if not self.enabled:
            logger.debug("ClamAV disabled, ping returning False")
            return False

        try:
            sock = self._get_socket()
            try:
                response = self._send_command(sock, "PING")
                is_alive = response == "PONG"
                logger.debug(f"ClamAV ping response: {response}")
                return is_alive
            finally:
                sock.close()
        except VirusScannerError as e:
            logger.warning(f"ClamAV ping failed: {e}")
            return False

    def get_version(self) -> Optional[str]:
        """
        Get ClamAV daemon version.

        Returns:
            Version string or None if unavailable
        """
        if not self.enabled:
            return None

        try:
            sock = self._get_socket()
            try:
                response = self._send_command(sock, "VERSION")
                logger.debug(f"ClamAV version: {response}")
                return response
            finally:
                sock.close()
        except VirusScannerError as e:
            logger.warning(f"ClamAV version check failed: {e}")
            return None

    def scan_file(self, file_bytes: bytes) -> VirusScanResult:
        """
        Scan file bytes for viruses/malware using ClamAV INSTREAM command.

        The INSTREAM protocol:
        1. Send "nINSTREAM\n" command
        2. Send file in chunks: 4-byte big-endian length + chunk data
        3. Send terminator: 4-byte zero (0x00000000)
        4. Read response

        Args:
            file_bytes: Raw file content to scan

        Returns:
            VirusScanResult with scan outcome

        Note:
            If ClamAV is disabled or unavailable, returns a clean result
            with a warning logged.
        """
        start_time = time.time()

        # If scanning is disabled, return clean result (stub behavior)
        if not self.enabled:
            scan_time_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "ClamAV disabled - file scan skipped",
                extra={"file_size_bytes": len(file_bytes)}
            )
            return VirusScanResult(
                is_clean=True,
                threat_name=None,
                scan_time_ms=scan_time_ms,
                error="ClamAV disabled"
            )

        try:
            sock = self._get_socket()
            try:
                # Send INSTREAM command
                sock.sendall(b"nINSTREAM\n")

                # Send file in chunks
                offset = 0
                while offset < len(file_bytes):
                    chunk = file_bytes[offset:offset + CLAMAV_CHUNK_SIZE]
                    chunk_len = len(chunk)

                    # Send 4-byte big-endian length followed by chunk data
                    sock.sendall(struct.pack(">I", chunk_len) + chunk)
                    offset += chunk_len

                # Send terminator (4 zero bytes)
                sock.sendall(struct.pack(">I", 0))

                # Read response
                response = sock.recv(4096).decode().strip()

                scan_time_ms = int((time.time() - start_time) * 1000)

                # Parse response
                # Clean: "stream: OK"
                # Infected: "stream: Eicar-Signature FOUND"
                if response.endswith("OK"):
                    logger.info(
                        f"ClamAV scan clean: {len(file_bytes)} bytes in {scan_time_ms}ms"
                    )
                    return VirusScanResult(
                        is_clean=True,
                        threat_name=None,
                        scan_time_ms=scan_time_ms
                    )
                elif "FOUND" in response:
                    # Extract threat name: "stream: ThreatName FOUND"
                    threat_name = response.replace("stream: ", "").replace(" FOUND", "")
                    logger.warning(
                        f"ClamAV detected threat: {threat_name} in {len(file_bytes)} bytes"
                    )
                    return VirusScanResult(
                        is_clean=False,
                        threat_name=threat_name,
                        scan_time_ms=scan_time_ms
                    )
                elif "ERROR" in response:
                    logger.error(f"ClamAV scan error: {response}")
                    return VirusScanResult(
                        is_clean=True,  # Fail open - don't block on scan errors
                        threat_name=None,
                        scan_time_ms=scan_time_ms,
                        error=response
                    )
                else:
                    logger.warning(f"Unexpected ClamAV response: {response}")
                    return VirusScanResult(
                        is_clean=True,  # Fail open
                        threat_name=None,
                        scan_time_ms=scan_time_ms,
                        error=f"Unexpected response: {response}"
                    )

            finally:
                sock.close()

        except VirusScannerError as e:
            scan_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"ClamAV scan failed: {e}")

            # Fail open - don't block uploads if ClamAV is unavailable
            return VirusScanResult(
                is_clean=True,
                threat_name=None,
                scan_time_ms=scan_time_ms,
                error=str(e)
            )

        except Exception as e:
            scan_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Unexpected error during virus scan: {e}", exc_info=True)

            # Fail open
            return VirusScanResult(
                is_clean=True,
                threat_name=None,
                scan_time_ms=scan_time_ms,
                error=str(e)
            )
