from opensearchpy import OpenSearch
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

        opensearch_client_information = self.client.info()
        print(f"OpenSearch connection information: {self.username}@[{self.username}'s password]{self.host}:{self.port}")
        print(f"Welcome to {opensearch_client_information["version"]["distribution"]} {opensearch_client_information["version"]["number"]}!")

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
        
        # Forward data
        document = etw_event[1]
        response = self.client.index(
            index = index,
            body = document,
            refresh = True
        )

        if response["_shards"]["failed"] == 0:
            sysmon_log_byte = len(str(document))
            document_id = response["_id"]
            document_result = response["result"]
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            print(f"[{current_time}] Documment#{document_id} --({document_result})--> index#{index} ({sysmon_log_byte:-5} bytes)")