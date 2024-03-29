import etw
import subprocess
import re
import time
from opensearch.opensearchConnector import OpenSearchConnector

class SysmonETWSession(etw.ETW):

    # Initializing the ETW session for Sysmon
    def __init__ (self, sysmon_provider:str = "Microsoft-Windows-Sysmon", service:str = "default", **kwargs) -> None:
        self.sysmon_provider = sysmon_provider
        self.sysmon_provider_guid = self.get_etw_guid(self.sysmon_provider)
        print("ETW Session started...")
        print(f"Sysmon Provider: {self.sysmon_provider}")
        print(f"Sysmon Provider GUID: {self.sysmon_provider_guid}")

        self.etw_sysmon_provider = [etw.ProviderInfo(self.sysmon_provider, 
                                                     etw.GUID(self.sysmon_provider_guid))]
        if service == "opensearch":
            self.endpoint = kwargs.get("endpoint")
            self.account = kwargs.get("account")
            self.index = kwargs.get("index")
            
            self.etw_session = etw.ETW(providers = self.etw_sysmon_provider, 
                                       event_callback = self.etw_callback_opensearch)
            self.opensearch_connector = OpenSearchConnector(endpoint = self.endpoint, 
                                                            account = self.account)
            self.opensearch_connector.create_index_if_not_exist(index = self.index)
        else:
            self.etw_session = etw.ETW(providers = self.etw_sysmon_provider, 
                                       event_callback = self.etw_callback_default)

    # Get the GUID of the ETW provider from logman query
    def get_etw_guid(self, provider:str) -> str:
        cmd = f"logman query providers {provider}"
        output = subprocess.check_output(cmd, shell = True).decode("utf-8")
        guid = re.search(r'{.*}', output).group(0)
        return guid
    
    # Callback function as default
    def etw_callback_default(self, event:any) -> None:
        print(event)

    # Callback function for OpenSearch
    def etw_callback_opensearch(self, event:any) -> None:
        self.opensearch_connector.index(etw_event = event, index = self.index)

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