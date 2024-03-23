import etw
import subprocess
import re
import time

# Query logman for the GUID of the provider
def get_etw_guid(provider:str) -> str:
    cmd = f"logman query providers {provider}"
    output = subprocess.check_output(cmd, shell=True).decode()
    guid = re.search(r'{.*}', output).group(0)
    return guid

def etw_callback(event:any) -> None:
    print(event)


def start(provider:str) -> None:
    provider_guid = get_etw_guid(provider)
    print(f"Provider: {provider}")
    print(f"Provider GUID: {provider_guid}")
    etw_sysmon_provider = [etw.ProviderInfo(provider, etw.GUID(provider_guid))]
    job = etw.ETW(providers=etw_sysmon_provider, event_callback=etw_callback)
    job.start()
    time.sleep(5)
    job.stop()

start("Microsoft-Windows-Sysmon")