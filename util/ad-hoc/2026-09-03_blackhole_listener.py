#!/usr/bin/env python
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   JuniperML
# Application:   util/ad-hoc
# Purpose:       TCP black-hole listener — accepts connections and never replies
#
# Author:        Paul Calnon
# Version:       0.1.0
# File Name:     2026-09-03_blackhole_listener.py
# File Path:     ${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/
#
# Date Created:  2026-09-03
# Last Modified: 2026-09-03
#
# License:       MIT License
# Copyright:     Copyright (c) 2024,2025,2026 Paul Calnon
#
# Description:
#     Stands in for a HUNG upstream service. A stopped service refuses connections
#     (ECONNREFUSED, immediate); a hung one completes the TCP handshake and then never
#     sends a byte, so the client blocks until its READ timeout rather than failing fast.
#     Those two failure modes differ by ~41x in cost for juniper-canopy's cascor client
#     (3.0 s refused vs an arithmetically-derived ~123 s black-holed), and the difference
#     decides X7's severity. This listener makes the second measurable.
#
#     Accepts every connection, holds it open, sends nothing, and never closes. Connections
#     are retained so the socket is not reset when the handle is garbage collected.
#
#####################################################################################################################################################################################################
# Notes:
#     - Bind to loopback only. Run in the foreground or with nohup; Ctrl-C / SIGTERM stops it.
#     - Deliberately dependency-free so it can run under any environment's python3.
#
#####################################################################################################################################################################################################

"""Accept TCP connections on a port and never respond, emulating a hung service."""

from __future__ import annotations

import socket
import sys
import threading


def _hold(conn: socket.socket) -> None:
    """Retain a connection forever without reading or writing it."""
    # No recv/send: the peer's request sits unanswered until its own read timeout.
    threading.Event().wait()


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8208
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", port))
    server.listen(128)
    print(f"black-hole listening on 127.0.0.1:{port} (accepts, never replies)", flush=True)

    held: list[socket.socket] = []  # keep references so nothing is closed by GC
    while True:
        conn, addr = server.accept()
        held.append(conn)
        print(f"accepted {addr} (held={len(held)})", flush=True)
        threading.Thread(target=_hold, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    raise SystemExit(main())
