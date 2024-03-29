from opensearchpy import OpenSearch
from consoledraw import Console
import datetime

class OpenSearchConnector:

    def __init__(self, endpoint:str, account:str) -> None:
        assert ":" in endpoint,                 "Endpoint should be in IP:port format"
        assert len(endpoint.split(":")) == 2,   "Endpoint should be in IP:port format"

        assert ":" in account,                  "Account should be in username:password format"
        assert len(account.split(":")) == 2,    "Account should be in username:password format"

        self.host = endpoint.split(":")[0]
        self.port = int(endpoint.split(":")[1])
        if self.port != 9200:
            print("OpenSearch's REST API port is 9200 as default. Check the port number if you are using a different port.")
        self.username = account.split(":")[0]
        self.password = account.split(":")[1] 

        self.client = OpenSearch(
            hosts = [{"host": self.host, "port": self.port}],
            http_auth = (self.username, self.password),
            http_compress = True,
            use_ssl = True,
            verify_certs = False,
            ssl_assert_hostname = False,
            ssl_show_warn = False
        )

        # Try to establish the connection to OpenSearch
        try:
            opensearch_client_information = self.client.info()
            print(f"OpenSearch connection information: {self.username}@[{self.username}'s password]{self.host}:{self.port}")
            print(f"Welcome to {opensearch_client_information["version"]["distribution"]} {opensearch_client_information["version"]["number"]}!")
        except Exception as exception:
            print(f"Failed to connect to OpenSearch service at {self.host}:{self.port} with {self.username}:[{self.username}'s password]")
            print(f"Exception message: {exception}")
            exit(-1)

        self.total_document_count = 0
        self.total_document_bytes = 0
        self.delinquent_document_count = 0
        self.delinquent_document_bytes = 0
        self.console = Console()        # For pretty console output and update

        self.latest_forwarding_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        self.latest_forwarded_document_id = None

    # Create the index for ETW events only if the index does not exist
    def create_index_if_not_exist(self, index:str) -> None:
        assert index, "Index should be provided"
        if not self.client.indices.exists(index = index):
            index_body = {
                "mappings": { 
                    "properties": {
                    "EventHeader": {
                        "properties": {
                        "Size": { "type": "integer" },
                        "HeaderType": { "type": "integer" },
                        "Flags": { "type": "integer" },
                        "EventProperty": { "type": "integer" },
                        "ThreadId": { "type": "integer" },
                        "ProcessId": { "type": "integer" },
                        "TimeStamp": { "type": "long" },
                        "ProviderId": { "type": "keyword" },
                        "EventDescriptor": {
                            "properties": {
                            "Id": { "type": "integer" },
                            "Version": { "type": "integer" },
                            "Channel": { "type": "integer" },
                            "Level": { "type": "integer" },
                            "Opcode": { "type": "integer" },
                            "Task": { "type": "integer" },
                            "Keyword": { "type": "text" }
                            }
                        },
                        "KernelTime": { "type": "integer" },
                        "UserTime": { "type": "integer" },
                        "ActivityId": { "type": "keyword" }
                        }
                    },
                    "Task Name": { "type": "text" },
                    "RuleName": { "type": "text" },
                    "UtcTime": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss.SSS" },
                    "ProcessGuid": { "type": "keyword" },
                    "ProcessId": { "type": "keyword" },
                    "Image": { "type": "text" },
                    "TargetFilename": { "type": "text" },
                    "CreationUtcTime": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss.SSS" },
                    "PreviousCreationUtcTime": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss.SSS" },
                    "User": { "type": "text" },
                    "Description": { "type": "text" }
                    }
                }
            }

            response = self.client.indices.create(index=index, body=index_body)
            if response["acknowledged"] == True:
                print(f"Index '{index}' is created; Response: {response}")
            else:
                raise Exception(f"Index '{index}' is not created; Response: {response}")
        else:
            print(f"Index '{index}' already exists, skipping the creation...")

    # Insert the event to OpenSearch (indexing)
    def index(self, etw_event:any, index:str) -> None:
        assert etw_event,   "ETW event should be provided"
        assert index,       "Index should be provided"
        
        # Forward data with exception handling
        try:
            document = etw_event[1]
            response = self.client.index(
                index = index,
                body = document,
                refresh = True
            )

            if response["_shards"]["failed"] == 0:
                sysmon_log_byte = len(str(document))
                self.latest_forwarded_document_id = response["_id"]
                self.latest_forwarding_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                self.total_document_count += 1
                self.total_document_bytes += sysmon_log_byte
                
                # Prepare the formatted strings
                lines = [
                    "*** Sysmon ETW is being forwarded to OpenSearch (successful) ***",
                    "Target:                        {}:{}(Index: {})".format(self.host, self.port, index),
                    "Latest forwarding time:        {}".format(self.latest_forwarding_time),
                    "Latest transacted document ID: {:}".format(self.latest_forwarded_document_id),
                    "Total document sent:           {:>15,} Docs".format(self.total_document_count),
                    "Total bytes sent:              {:>15,} Byte".format(self.total_document_bytes)
                ]

                if self.delinquent_document_count > 0:
                    # If there are delinquent documents to be sent and
                    # the agent is forwarding the document successfully,
                    # It's resolving the delinquent documents. Print the information that the delinquency is being resolved.
                    lines.append("Reamined delinquent documents: {:>15,} Docs".format(self.delinquent_document_count))
                    lines.append("Remained bytes delinquent:     {:>15,} Byte".format(self.delinquent_document_bytes))
                    self.delinquent_document_count -= 1
                    self.delinquent_document_bytes -= sysmon_log_byte

                format_string = "\n".join(lines)

                # Print the formatted output
                with self.console:
                    self.console.print(format_string)

        except Exception as exception:
            self.delinquent_document_count += 1
            self.delinquent_document_bytes += len(str(document))
            
            # Prepare the formatted strings
            lines = [
                "*** Sysmon ETW is being forwarded to OpenSearch (failed) ***",
                "Target:                        {}:{}(Index: {})".format(self.host, self.port, index),
                "Latest forwarding time:        {}".format(self.latest_forwarding_time),
                "Latest transacted document ID: {:}".format(self.latest_forwarded_document_id),
                "Total document sent:           {:>15,} Docs".format(self.total_document_count),
                "Total bytes sent:              {:>15,} Byte".format(self.total_document_bytes),
                "Total delinquent document:     {:>15,} Docs".format(self.delinquent_document_count),
                "Total bytes delinquent:        {:>15,} Byte".format(self.delinquent_document_bytes),
                "Exception:                     {}".format(exception)
            ]

            format_string = "\n".join(lines)

            # Print the formatted output
            with self.console:
                self.console.print(format_string)