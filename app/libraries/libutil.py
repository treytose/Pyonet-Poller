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
    
    
  async def scan_device_storage(self, deviceid):
    device = await db.fetchone("SELECT * FROM device WHERE deviceid = :deviceid", {"deviceid": deviceid})

    if device is None:
        return False
    
    hostname = device.hostname
    community = device.snmp_community
    port = device.snmp_port
    
    # OID for storage types
    storage_types_oid = '.1.3.6.1.2.1.25.2.3.1.2'
    # OID for storage description
    storage_desc_oid = '.1.3.6.1.2.1.25.2.3.1.3'
    # OID for allocation units
    allocation_units_oid = '.1.3.6.1.2.1.25.2.3.1.4'
    # OID for storage size
    storage_size_oid = '.1.3.6.1.2.1.25.2.3.1.5'
    # OID for storage used
    storage_used_oid = '.1.3.6.1.2.1.25.2.3.1.6'
    
    storage_info = {}

    # Function to perform SNMP get next request
    def get_bulk_auto(target, oids):
        for (errorIndication,
             errorStatus,
             errorIndex,
             varBinds) in nextCmd(SnmpEngine(),
                                  CommunityData(community),
                                  UdpTransportTarget((target, port)),
                                  ContextData(),
                                  *oids,
                                  lexicographicMode=False):

            if errorIndication:
                print(errorIndication)
                break
            elif errorStatus:
                print('%s at %s' % (errorStatus.prettyPrint(),
                                    errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                break
            else:
                for varBind in varBinds:                    
                    yield varBind

    def extract_unique_identifier(oid):
        """
        Extracts the unique identifier (index) from the OID string.
        Assumes that the index is the last part of the OID.
        """
        return oid.split('.')[-1]

    # Retrieve storage information
    for varBind in get_bulk_auto(hostname, [ObjectType(ObjectIdentity(storage_types_oid)),
                                      ObjectType(ObjectIdentity(storage_desc_oid)),
                                      ObjectType(ObjectIdentity(allocation_units_oid)),
                                      ObjectType(ObjectIdentity(storage_size_oid)),
                                      ObjectType(ObjectIdentity(storage_used_oid))]):
        oid, value = varBind
        oid_str = str(oid)
        if not oid_str.startswith("."):
            oid_str = "." + oid_str
            
        unique_id = extract_unique_identifier(oid_str)
        storage_info.setdefault(unique_id, {})['type'] = str(value)
                            
        if oid_str.startswith(storage_desc_oid):
            # storage_info[oid_str] = {'desc': str(value)}
            storage_info.setdefault(unique_id, {})['desc'] = str(value)
        elif oid_str.startswith(allocation_units_oid):
            storage_info.setdefault(unique_id, {})['alloc_units'] = int(value)
        elif oid_str.startswith(storage_size_oid):
            storage_info.setdefault(unique_id, {})['size'] = int(value)
            #storage_info[oid_str.replace(storage_size_oid, storage_desc_oid)]['size'] = int(value)
        elif oid_str.startswith(storage_used_oid):
            storage_info.setdefault(unique_id, {})['used'] = int(value)
            
        storage_info[unique_id]['desc_oid'] = storage_desc_oid + '.' + unique_id
        storage_info[unique_id]['alloc_units_oid'] = allocation_units_oid + '.' + unique_id
        storage_info[unique_id]['size_oid'] = storage_size_oid + '.' + unique_id
        storage_info[unique_id]['used_oid'] = storage_used_oid + '.' + unique_id                
                    

    # Calculate and print results
    for key, val in storage_info.items():
        max_avail = val['size'] * val['alloc_units']
        used = val['used'] * val['alloc_units']
        
    # convert to list with oid as key
    storage_info_list = []
    for k,v in storage_info.items():
        storage_info_list.append(v)
        
    # calculate the percentage used for each storage
    for storage in storage_info_list:
        storage['percent_used'] = round((storage['used'] * storage['alloc_units']) / (storage['size'] * storage['alloc_units']), 2) * 100

    return storage_info_list
