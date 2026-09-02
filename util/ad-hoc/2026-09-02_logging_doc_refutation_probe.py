#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (adversarial review of the 2026-09-02 logging docs)
Application: ad-hoc probe
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: re-derive N-3 from the running code rather than from a code read.

Answers, empirically, at cascor HEAD 70edfc4:
  * what `Logger.isEnabledFor(level=N)` actually compares against,
  * whether the *emit* path (`_log_at_level` -> `_filter_by_level`) reads the
    same state that `isEnabledFor` reads,
  * whether the reconciliation doc's causal story for VERBOSE actually holds.

Read-only against the cascor tree; writes its log to a scratch dir via
JUNIPER_CASCOR_LOG_DIR.
"""
import os
import sys

CASCOR_SRC = "/home/pcalnon/Development/python/Juniper/juniper-cascor/src"
sys.path.insert(0, CASCOR_SRC)

from log_config.logger.logger import Logger  # noqa: E402


def state(tag):
    print(f"--- {tag}")
    print(f"    _log_level                 = {Logger._log_level!r}")
    print(f"    get_level()                = {Logger.get_level()!r}")
    print(f"    _level_logger_name         = {Logger._level_logger_name!r}")
    print(f"    _level_logger_config       = {Logger._level_logger_config!r}")
    print(f"    is_configured()            = {Logger.is_configured()!r}")
    emit_level = Logger._get_log_level_check(
        config_lvl=Logger._level_logger_config,
        norm_lvl=Logger._level_logger_name,
    )(Logger.is_configured())
    print(f"    EMIT-PATH effective level  = {emit_level!r}")
    for name, num in (("TRACE", 1), ("VERBOSE", 5), ("mystery-8", 8), ("DEBUG", 10), ("INFO", 20)):
        g = Logger.isEnabledFor(level=num)
        e = Logger._filter_by_level(level=num, log_level=emit_level)
        print(f"    isEnabledFor({num:>2}) = {str(g):<5}   _filter_by_level({name}) = {e}")


print("_level_numbers:", Logger._level_numbers)
print()
state("A: fresh import, no configuration, no set_level")
print()

Logger.set_level("VERBOSE")
state("B: after Logger.set_level('VERBOSE')")
print()

Logger.set_level("TRACE")
state("C: after Logger.set_level('TRACE')")
print()

Logger.set_configured()
state("D: after set_configured() with _log_level=TRACE")
