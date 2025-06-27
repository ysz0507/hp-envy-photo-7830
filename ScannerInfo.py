import requests
import re
from enum import Enum
from time import localtime, strftime
import os
import time
from dotenv import load_dotenv
load_dotenv()

class ScannerAdfState(Enum):
    EMPTY = "ScannerAdfEmpty"
    LOADED = "ScannerAdfLoaded"
    JAMMED = "ScannerAdfMispick"

class ScannerState(Enum):
    IDLE = "Idle"
    PROCESSING = "Processing"
    STOPPED = "Stopped"

class JobState(Enum):
    COMPLETED = "Completed"
    PROCESSING = "Processing"
    PENDING = "Pending" # wait for ADF to start scanning
    FAILED = "Aborted"

class ScannerInfo:
    def __init__(self):
        self.target_dir = "out"
        self.ip = os.getenv('IP_ADDRESS')
        self.target_dir = os.getenv('TARGET_DIR')
        self.file_format = os.getenv('FILE_FORMAT')
        url = f"http://{self.ip}/eSCL/ScannerStatus"
        r = requests.get(url)
        self.response = r.text
        self.adf_state = re.search(r'<scan:AdfState>(.+)</scan:AdfState>', r.text).group(1)
        self.scanner_state = re.search(r'<pwg:State>(.+)</pwg:State>', r.text).group(1)
        self.last_job_id = re.search(r'<pwg:JobUuid>(.+)</pwg:JobUuid>', r.text)
        if self.last_job_id:
            self.last_job_id = self.last_job_id.group(1)
        self.last_job_state = re.search(r'<pwg:JobState>(.+)</pwg:JobState>', r.text)
        if self.last_job_state:
            self.last_job_state = self.last_job_state.group(1)

    def print_info(self, include_response=False):
        print(f"ADF State: {self.adf_state}")
        print(f"Scanner State: {self.scanner_state}")
        print(f"Last Job ID: {self.last_job_id}")
        print(f"Last Job State: {self.last_job_state}")
        if include_response:
            print("Full Response:")
            print(self.response)

    def is_adf_loaded(self):
        return self.adf_state == ScannerAdfState.LOADED.value
    
    def is_scanner_idle(self):
        return self.scanner_state == ScannerState.IDLE.value

    def start_glass_scan(self):
        url = f"http://{self.ip}/eSCL/ScanJobs"
        glass_payload = """
        <scan:ScanSettings xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03"
            xmlns:copy="http://www.hp.com/schemas/imaging/con/copy/2008/07/07"
            xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/"
            xmlns:dd3="http://www.hp.com/schemas/imaging/con/dictionaries/2009/04/06"
            xmlns:fw="http://www.hp.com/schemas/imaging/con/firewall/2011/01/05"
            xmlns:scc="http://schemas.hp.com/imaging/escl/2011/05/03"
            xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
            <pwg:Version>2.1</pwg:Version>
            <scan:Intent>Document</scan:Intent>
            <pwg:ScanRegions>
                <pwg:ScanRegion>
                    <pwg:Height>3507</pwg:Height>
                    <pwg:Width>2481</pwg:Width>
                    <pwg:XOffset>0</pwg:XOffset>
                    <pwg:YOffset>0</pwg:YOffset>
                </pwg:ScanRegion>
            </pwg:ScanRegions>
            <pwg:InputSource>Platen</pwg:InputSource>
            <scan:DocumentFormatExt>application/pdf</scan:DocumentFormatExt>
            <scan:XResolution>300</scan:XResolution>
            <scan:YResolution>300</scan:YResolution>
            <scan:ColorMode>RGB24</scan:ColorMode>
            <scan:CompressionFactor>35</scan:CompressionFactor>
            <scan:Brightness>600</scan:Brightness>
            <scan:Contrast>600</scan:Contrast>
        </scan:ScanSettings>"""
        requests.post(url, glass_payload)

    def start_adf_scan(self):
        url = f"http://{self.ip}/eSCL/ScanJobs"
        glass_payload = """
        <scan:ScanSettings xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03"
            xmlns:copy="http://www.hp.com/schemas/imaging/con/copy/2008/07/07"
            xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/"
            xmlns:dd3="http://www.hp.com/schemas/imaging/con/dictionaries/2009/04/06"
            xmlns:fw="http://www.hp.com/schemas/imaging/con/firewall/2011/01/05"
            xmlns:scc="http://schemas.hp.com/imaging/escl/2011/05/03"
            xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
            <pwg:Version>2.1</pwg:Version>
            <scan:Intent>Document</scan:Intent>
            <pwg:ScanRegions>
                <pwg:ScanRegion>
                    <pwg:Height>3507</pwg:Height>
                    <pwg:Width>2481</pwg:Width>
                    <pwg:XOffset>0</pwg:XOffset>
                    <pwg:YOffset>0</pwg:YOffset>
                </pwg:ScanRegion>
            </pwg:ScanRegions>
            <pwg:InputSource>Feeder</pwg:InputSource>
            <scan:DocumentFormatExt>application/pdf</scan:DocumentFormatExt>
            <scan:XResolution>300</scan:XResolution>
            <scan:YResolution>300</scan:YResolution>
            <scan:ColorMode>RGB24</scan:ColorMode>
            <scan:Duplex>false</scan:Duplex>
            <scan:CompressionFactor>15</scan:CompressionFactor>
            <scan:Brightness>1000</scan:Brightness>
            <scan:Contrast>1000</scan:Contrast>
        </scan:ScanSettings>"""
        requests.post(url, glass_payload)
    
    def start_download(self, use_subfolder=False):
        url = f"http://{self.ip}/eSCL/ScanJobs/{self.last_job_id}/NextDocument"
        r = requests.get(url)
        if r.status_code != 200:
            raise IOError(f"Failed to download document: {r.status_code} - {r.text}")
        
        path = self.target_dir
        if use_subfolder:
            path += "/double-sided"

        filename = strftime(self.file_format, localtime()) + ".pdf"
        with open(f"{path}/{filename}", mode="wb") as file:
            file.write(r.content)

def scan_document(use_subfolder=False):
    while True:
        scanner = ScannerInfo()
        if scanner.is_adf_loaded() and scanner.is_scanner_idle():
            print("\nADF is loaded and scanner is idle. Starting scan.")
            scanner.start_adf_scan()
            print("Start file download")
            ScannerInfo().start_download(use_subfolder=use_subfolder)
            return
        time.sleep(5)
        print(".", end="", flush=True)

if __name__ == "__main__":
    while True:
        command = input("Enter new command: [e]xit, [s]ingle, [d]uplex\n")
        if command not in ("e", "s", "d"):
            print("Invalid command")
            continue
        if command == "e":
            print("Exit script")
            break
        
        if command == "s":
            print("Insert single-sided stack into adf")
            scan_document(use_subfolder=False)
        if command == "d":
            print("Insert stack for first pass")
            scan_document(use_subfolder=True)
            print("Insert stack for second pass")
            scan_document(use_subfolder=True)