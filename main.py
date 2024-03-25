from sysmonETWSession import SysmonETWSession
import argparse

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
    args = argument_parser.parse_args()

    # argparse's argument set validation
    if args.opensearch and not args.endpoint and not args.account and not args.index:
        argument_parser.error("--endpoint, --account, --index are required options when --opensearch is enabled")

    # Set option to SysmonETWSession
    if args.opensearch:
        sysmon_etw = SysmonETWSession(service = "opensearch", 
                                      endpoint = args.endpoint,
                                      account = args.account,
                                      index = args.index)
    else:
        sysmon_etw = SysmonETWSession()
    
    sysmon_etw.run(testing = args.testing)