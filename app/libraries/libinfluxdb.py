from datetime import datetime
from app import INFLUXDB_TOKEN, INFLUX_DB_HOST, INFLUX_DB_PORT, INFLUX_DB_ORG, INFLUX_DB_BUCKET
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxDB:
  
  def __init__(self):
    self.client = InfluxDBClient(url=f"http://{INFLUX_DB_HOST}:{INFLUX_DB_PORT}", token=INFLUXDB_TOKEN, org=INFLUX_DB_ORG)
    self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
    
  def __del__(self):
    self.client.close()
    
  async def store_check_result(self, device_name, check_name, value, check_group_name = None):
    point = Point("check_result").tag("device", device_name).tag("check", check_name).field("value", value)
    if check_group_name:
      point.tag("check_group", check_group_name)
      
    self.write_api.write(bucket=INFLUX_DB_BUCKET, record=point)
    
    print(f"[{datetime.now().isoformat()}] Stored check result for device '{device_name}' check '{check_name}' with value '{value}'")
  