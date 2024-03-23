import etw
import subprocess
import re
import time

class SysmonETWSession(etw.ETW):

    # Initializing the ETW session for Sysmon
    def __init__ (self, sysmon_provider:str = "Microsoft-Windows-Sysmon") -> None:
        self.sysmon_provider = sysmon_provider
        self.sysmon_provider_guid = self.get_etw_guid(self.sysmon_provider)
        self.etw_sysmon_provider = [etw.ProviderInfo(self.sysmon_provider, etw.GUID(self.sysmon_provider_guid))]
        super().__init__(providers=self.etw_sysmon_provider, event_callback=self.etw_callback)

    # Get the GUID of the ETW provider
    def get_etw_guid(self, provider:str) -> str:
        cmd = f"logman query providers {provider}"
        output = subprocess.check_output(cmd, shell=True).decode()
        guid = re.search(r'{.*}', output).group(0)
        return guid
    
    # Callback function to print the ETW events
    def etw_callback(self, event:any) -> None:
        print(event)

    # Start the ETW session
    def run(self, testing=True):
        self.start()
        if testing:
            time.sleep(5)
            self.stop()
        else:
            pass

if __name__ == "__main__":
    sysmon_etw = SysmonETWSession()
    sysmon_etw.run(testing=True)