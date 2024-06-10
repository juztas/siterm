#!/usr/bin/env python3
"""
Config Fetcher from Github.

Authors:
  Justas Balcas jbalcas (at) caltech.edu

Date: 2022/05/19
"""
import sys
import time
import copy
import datetime
import os
import shutil
import filecmp

from SiteRMLibs.MainUtilities import (getLoggingObject, getWebContentFromURL,
                                      getFullUrl, getHostname, publishToSiteFE)
from SiteRMLibs.GitConfig import GitConfig, getGitConfig
from yaml import safe_load as yload
from yaml import safe_dump as ydump


class ConfigFetcher():
    """Config Fetcher from Github."""
    def __init__(self, logger):
        self.logger = logger
        self.gitObj = GitConfig()
        self.config = getGitConfig()
        self.forceRefresh = False

    def refreshthread(self, *_args):
        """Call to refresh thread for this specific class and reset parameters"""
        self.gitObj = GitConfig()
        self.config = None

    def _fetchFile(self, name, url):
        def retryPolicy(outObj, retries=3):
            if 'status_code' in outObj and outObj['status_code'] == -1:
                self.logger.debug(f'Got -1 (Timeout usually error. Will retry up to 3 times (5sec sleep): {outObj}')
                retries -= 1
            elif outObj.status_code != 200:
                self.logger.debug(f'Got status code {outObj.status_code} for {url}')
                retries -= 1
            else:
                return -1
            if retries == 0:
                self.logger.debug(f'Got too many retries. Will stop retrying to get config file: {outObj}')
            else:
                time.sleep(5)
            return retries
        output = {}
        datetimeNow = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)
        filename = f"/tmp/{datetimeNow.strftime('%Y-%m-%d-%H')}-{name}.yaml"
        prevfilename = f"/tmp/{datetimeNow.strftime('%Y-%m-%d-%H')}-{name}.yaml"  # Will be overwritten in else if file not exists
        if os.path.isfile(filename):
            self.logger.info(f'Config files are not yet needed for update. For {name} from {url}')
            with open(filename, 'r', encoding='utf-8') as fd:
                output = yload(fd.read())
        else:
            self.logger.info(f'Fetching new config file for {name} from {url}')
            datetimelasthour = datetimeNow - datetime.timedelta(hours=1)
            prevfilename = f"/tmp/{datetimelasthour.strftime('%Y-%m-%d-%H')}-{name}.yaml"
            print(f'Receiving new file from GIT for {name}')
            retries = 3
            while retries > 0:
                outObj = getWebContentFromURL(url)
                retries = retryPolicy(outObj, retries)
                if retries == 0:
                    output = {}
                elif retries == -1:
                    output = yload(outObj.text)
                else:
                    continue
                with open(filename, 'w', encoding='utf-8') as fd:
                    fd.write(ydump(output))
                try:
                    shutil.copy(filename, f'/tmp/siterm-link-{name}.yaml')
                    if os.path.isfile(prevfilename):
                        self.logger.info(f'Remove previous old cache file {prevfilename}')
                        os.remove(prevfilename)
                except IOError as ex:
                    self.logger.info(f'Got IOError: {ex}')
        return output, filename, prevfilename

    def refreshNeeded(self, newfname, oldfname):
        """Check if refresh is needed for specific file."""
        if newfname == oldfname:
            return
        if not filecmp.cmp(newfname, oldfname):
            self.logger.info(f'Got new config file. Will update {newfname} and {oldfname}')
            self.forceRefresh = True

    def addDBRefresh(self):
        """Add DB refresh to the list."""
        # pylint: disable=W0703
        if not self.forceRefresh:
            return
        self.forceRefresh = False
        try:
            fullUrl = getFullUrl(self.config, self.gitObj.config['SITENAME'])
            fullUrl += "/sitefe"
            dic = {"servicename": "ALL", "hostname": getHostname()}
            publishToSiteFE(dic, fullUrl, "/json/frontend/serviceaction", "POST")
        except Exception:
            excType, excValue = sys.exc_info()[:2]
            self.logger.info(f"Error details in addDBRefresh. ErrorType: {str(excType.__name__)}, ErrMsg: {excValue}")

    def fetchMapping(self):
        """Fetch mapping file from Github"""
        url = f"{self.gitObj.getFullGitUrl()}/mapping.yaml"
        return self._fetchFile('mapping', url)

    def fetchAgent(self):
        """Fetch Agent config file from Github"""
        if self.gitObj.config['MAPPING']['type'] == 'Agent':
            url = self.gitObj.getFullGitUrl([self.gitObj.config['MAPPING']['config'], 'main.yaml'])
            _out, newfname, oldfname = self._fetchFile('Agent-main', url)
            self.refreshNeeded(newfname, oldfname)

    def fetchFE(self):
        """Fetch FE config file from Github"""
        if self.gitObj.config['MAPPING']['type'] == 'FE':
            url = self.gitObj.getFullGitUrl([self.gitObj.config['MAPPING']['config'], 'main.yaml'])
            _out, newfname, oldfname = self._fetchFile('FE-main', url)
            self.refreshNeeded(newfname, oldfname)
            url = self.gitObj.getFullGitUrl([self.gitObj.config['MAPPING']['config'], 'auth.yaml'])
            _out, newfname, oldfname = self._fetchFile('FE-auth', url)
            self.refreshNeeded(newfname, oldfname)
            url = self.gitObj.getFullGitUrl([self.gitObj.config['MAPPING']['config'], 'auth-re.yaml'])
            _out, newfname, oldfname = self._fetchFile('FE-auth-re', url)
            self.refreshNeeded(newfname, oldfname)

    def cleaner(self):
        """Clean files from /tmp/ directory"""
        datetimeNow = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)
        for name in ["mapping", "Agent-main", "FE-main", "FE-auth", "FE-auth-re"]:
            filename = f"/tmp/{datetimeNow.strftime('%Y-%m-%d-%H')}-{name}.yaml"
            if os.path.isfile(filename):
                os.remove(filename)
            filename = f'/tmp/siterm-link-{name}.yaml'
            if os.path.isfile(filename):
                os.remove(filename)
        # Once removed - reget configs
        self.startwork()

    def startwork(self):
        """Start Config Fetcher Service."""
        self.gitObj.getLocalConfig()
        mapping, newfname, oldfname = self.fetchMapping()
        if newfname != oldfname:
            self.logger.info('Got new mapping file. Will update mapping and fetch Agent and FE configs.')
        self.gitObj.config['MAPPING'] = copy.deepcopy(mapping[self.gitObj.config['MD5']])
        self.fetchAgent()
        self.fetchFE()
        # Instruct db to reload config files
        if self.forceRefresh:
            self.logger.info('Force refresh is needed. Will instruct DB to reload config files.')
            self.addDBRefresh()
            self.forceRefresh = False


if __name__ == "__main__":
    logObj = getLoggingObject(logType='StreamLogger', service='ConfigFetcher')
    cfgFecth = ConfigFetcher(logObj)
    cfgFecth.startwork()
