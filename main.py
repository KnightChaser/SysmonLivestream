import etw
import subprocess
import re
import time
import argparse

class SysmonETWSession(etw.ETW):

    # Initializing the ETW session for Sysmon
    def __init__ (self, sysmon_provider:str = "Microsoft-Windows-Sysmon") -> None:
        self.sysmon_provider = sysmon_provider
        self.sysmon_provider_guid = self.get_etw_guid(self.sysmon_provider)
        print("ETW Session started...")
        print(f"Sysmon Provider: {self.sysmon_provider}")
        print(f"Sysmon Provider GUID: {self.sysmon_provider_guid}")

        self.etw_sysmon_provider = [etw.ProviderInfo(self.sysmon_provider, 
                                                     etw.GUID(self.sysmon_provider_guid))]
        self.etw_session = etw.ETW(providers=self.etw_sysmon_provider, 
                                   event_callback=self.etw_callback)

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
        super().stop()

    # Start the ETW session
    def run(self, testing=True):
        self.etw_session.start()
        try:
            # If "--testing" mode is enabled, wait ETW session only for 5 seconds.
            if testing:
                time.sleep(5)
            # If "--testing" mode is not enabled, wait ETW session indefinitely.
            else:
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("Keyboard interrupt received...")
        finally:    
            self.etw_session.stop()
            print("ETW session stopped")

    # Signal handler to stop the ETW session
    def signal_handler(self) -> None:
        print("Stopping ETW session because of keyboard interrupt...")

if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--testing", 
                                 help="Testing mode", 
                                 action="store_true")
    args = argument_parser.parse_args()

    sysmon_etw = SysmonETWSession()
    sysmon_etw.run(testing=args.testing)