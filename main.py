import etw
import subprocess
import re
import time

class SysmonETWSession(etw.ETW):

    # Initializing the ETW session for Sysmon
    def __init__ (self, sysmon_provider:str = "Microsoft-Windows-Sysmon") -> None:
        self.sysmon_provider = sysmon_provider
        self.sysmon_provider_guid = self.get_etw_guid(self.sysmon_provider)
        print("ETW Session started...")
        print(f"Sysmon Provider: {self.sysmon_provider}")
        print(f"Sysmon Provider GUID: {self.sysmon_provider_guid}")
        self.etw_sysmon_provider = [etw.ProviderInfo(self.sysmon_provider, etw.GUID(self.sysmon_provider_guid))]
        self.etw_session = etw.ETW(providers=self.etw_sysmon_provider, event_callback=self.etw_callback)

    # Get the GUID of the ETW provider
    def get_etw_guid(self, provider:str) -> str:
        cmd = f"logman query providers {provider}"
        output = subprocess.check_output(cmd, shell=True).decode()
        guid = re.search(r'{.*}', output).group(0)
        return guid
    
    # Callback function to print the ETW events
    def etw_callback(self, event:any) -> None:
        print(event)

    # Stop the ETW session
    def stop(self):
        exit(0)

    # Start the ETW session
    def run(self, testing=True):
        self.etw_session.start()
        if testing:
            time.sleep(5)
            self.etw_session.stop()
            print("ETW session stopped")
        else:
            pass

if __name__ == "__main__":
    sysmon_etw = SysmonETWSession()
    sysmon_etw.run(testing=True)