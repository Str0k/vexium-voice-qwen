"""Run ONCE after creating the Tablestore instance in the Alibaba console."""
import os
import tablestore
from tablestore import OTSClient, TableMeta, TableOptions, ReservedThroughput, CapacityUnit

def get_client() -> OTSClient:
    return OTSClient(
        os.environ["TABLESTORE_ENDPOINT"],
        os.environ["TABLESTORE_ACCESS_KEY_ID"],
        os.environ["TABLESTORE_ACCESS_KEY_SECRET"],
        os.environ["TABLESTORE_INSTANCE"],
    )

TABLES = [
    # (table_name, [(pk_col, pk_type), ...])
    ("vx_events",   [("tenant", "STRING"), ("event_id", "STRING")]),
    ("vx_bookings", [("tenant", "STRING"), ("booking_id", "STRING")]),
    ("vx_callers",  [("tenant", "STRING"), ("phone", "STRING")]),
    ("vx_tenants",  [("tenant", "STRING")]),
]

def provision():
    client = get_client()
    opts = TableOptions(time_to_live=-1, max_version=1)
    throughput = ReservedThroughput(CapacityUnit(0, 0))
    for table_name, pk_schema in TABLES:
        schema_of_primary_key = [(col, col_type) for col, col_type in pk_schema]
        table_meta = TableMeta(table_name, schema_of_primary_key)
        client.create_table(table_meta, opts, throughput)
        print(f"Created table: {table_name}")

if __name__ == "__main__":
    provision()
