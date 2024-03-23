import etw
import time

def some_func():
    etwSysmonProvider = [etw.ProviderInfo("Microsoft-Windows-Sysmon", etw.GUID("{5770385F-C22A-43E0-BF4C-06F5698FFBD9}"))]
    job = etw.ETW(providers=etwSysmonProvider, event_callback=lambda event: print(event))
    job.start()
    time.sleep(5)
    job.stop()

some_func()