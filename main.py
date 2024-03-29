from sysmonETWSession import SysmonETWSession
import argparse
import subprocess
import sys
import os

if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--testing", 
                                 help = "Testing mode", 
                                 action = "store_true")
    argument_parser.add_argument("--opensearch",
                                 help = "Stream logs to OpenSearch database",
                                 action = "store_true")
    argument_parser.add_argument("--endpoint",
                                 help = "Endpoint to the target service (IP:Port)",
                                 type = str)
    argument_parser.add_argument("--account",
                                 help = "Account to the target service (username:password)",
                                 type = str)
    argument_parser.add_argument("--index",
                                 help = "Index name to store the logs",
                                 type = str)
    argument_parser.add_argument("--checkAndDeploySysmonOffline",
                                 help = "Check if Sysmon service is running or not. If not, deploy Sysmon service (sysmonExePath:sysmonConfigPath)",
                                 type = str)
    args = argument_parser.parse_args()

    # argparse's argument set validation
    if args.opensearch and not args.endpoint and not args.account and not args.index:
        argument_parser.error("--endpoint, --account, --index are required options when --opensearch is enabled")

    # Run ./deploySysmon.ps1 to check the status of the Sysmon service
    if getattr(sys, "frozen", False):
        script_path = os.path.join(sys._MEIPASS, "scripts/deploySysmon.ps1")
        powershell_execution_command = f"powershell.exe -ExecutionPolicy RemoteSigned -file {script_path}"
    else:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts/deploySysmon.ps1")
        powershell_execution_command = f"powershell.exe -ExecutionPolicy RemoteSigned -file {script_path}"

    if args.checkAndDeploySysmonOffline:
        if len(args.checkAndDeploySysmonOffline.split(":")) != 2:
            argument_parser.error("--deploy option requires sysmonExePath and sysmonConfigPath. (sysmonExePath:sysmonConfigPath)")

        sysmon_executable_path = args.checkAndDeploySysmonOffline.split(":")[0].replace("(", "").replace(")", "").replace("'", "").replace('"', "").strip()
        sysmon_config_path = args.checkAndDeploySysmonOffline.split(":")[1].replace("(", "").replace(")", "").replace("'", "").replace('"', "").strip()
        powershell_execution_command += f" -checkAndDeploySysmonOffline true -sysmonExePath {sysmon_executable_path} -sysmonConfigPath {sysmon_config_path}"
    else:
        powershell_execution_command += " -checkAndDeploySysmonOffline false"

    try:
        checker = subprocess.Popen(powershell_execution_command, stdout = sys.stdout)
        checker.communicate()[0]
        checker.wait()
        if checker.returncode != 0:
            print("Error during running Sysmon service checkup. Is the programming running with administrator privilege?")
            sys.exit(1) 

        # Set option to SysmonETWSession
        # Because SysmonETWSession requires Sysmon service registerd to logman, the previous step is necessary.
        if args.opensearch:
            sysmon_etw = SysmonETWSession(service = "opensearch", 
                                        endpoint = args.endpoint,
                                        account = args.account,
                                        index = args.index)
        else:
            sysmon_etw = SysmonETWSession()

        sysmon_etw.run(testing = args.testing)
    except Exception as exception:
        print(f"Error during running script: {exception}")
        sys.exit(1)