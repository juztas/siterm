#!/usr/bin/env python3
# pylint: disable=E1101
"""
Title                   : siterm
Author                  : Justas Balcas
Email                   : jbalcas (at) es (dot) net
@Copyright              : Copyright (C) 2024 Justas Balcas
Date                    : 2024/02/26
"""
from SiteRMLibs.BaseDebugAction import BaseDebugAction
from SiteRMLibs.CustomExceptions import BackgroundException

class RapidPing(BaseDebugAction):
    """RapidPing class"""
    def __init__(self, config, sitename, backgConfig):
        self.config = config
        self.sitename = sitename
        self.backgConfig = backgConfig
        self.requestdict = backgConfig.get('requestdict', {})
        self.service = "RapidPing"
        super().__init__()

    def main(self):
        """Main RapidPing work. Run RapidPing on switches."""
        self.logMessage(f"NOT IMPLEMENTED call {self.backgConfig} to run rapid ping on switches", "warning")
        raise BackgroundException("NOT IMPLEMENTED! -1")
