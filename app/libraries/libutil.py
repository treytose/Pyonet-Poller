from app import db
from pysnmp.hlapi import *

class Util:
  def __init__(self):
    pass
  
  async def scan_device_interfaces(self, deviceid):
    device = await db.fetchone("SELECT * FROM device WHERE deviceid = :deviceid", {"deviceid": deviceid})
    
    if device is None:
      return False
    
    hostname = device.hostname
    community = device.snmp_community
    port = device.snmp_port
    oids = {
        'ifName': '1.3.6.1.2.1.31.1.1.1.1',
        'ifHCInOctets': '1.3.6.1.2.1.31.1.1.1.6',
        'ifHCOutOctets': '1.3.6.1.2.1.31.1.1.1.10'
    }
    results = {key: {} for key in oids.keys()}

    for oid_name, oid_base in oids.items():
        for (errorIndication,
             errorStatus,
             errorIndex,
             varBinds) in nextCmd(SnmpEngine(),
                                   CommunityData(community),
                                   UdpTransportTarget((hostname, port)),
                                   ContextData(),
                                   ObjectType(ObjectIdentity(oid_base)),
                                   lexicographicMode=False):
            
            if errorIndication or errorStatus:
                return {"error": str(errorIndication or errorStatus)}

            for varBind in varBinds:
                oid, value = varBind
                results[oid_name][str(oid)] = str(value)

    interface_data = {}
    for oid in results['ifName'].keys():
        ifIndex = oid.split('.')[-1]
        interface_data[results['ifName'][oid]] = {
            'ifHCInOctetsOID': f'1.3.6.1.2.1.31.1.1.1.6.{ifIndex}',
            'ifHCInOctetsValue': results['ifHCInOctets'].get(f'1.3.6.1.2.1.31.1.1.1.6.{ifIndex}', 'N/A'),
            'ifHCOutOctetsOID': f'1.3.6.1.2.1.31.1.1.1.10.{ifIndex}',
            'ifHCOutOctetsValue': results['ifHCOutOctets'].get(f'1.3.6.1.2.1.31.1.1.1.10.{ifIndex}', 'N/A')
        }
    
    return interface_data
    
    