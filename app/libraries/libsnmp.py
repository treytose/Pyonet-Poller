import asyncio
from pysnmp.hlapi.asyncio import getCmd, CommunityData, UdpTransportTarget, ObjectType, ObjectIdentity, ContextData, SnmpEngine
from pysnmp.proto import rfc1902

async def get_snmp_value(oid, host, port, community):
    """
    Perform an asynchronous SNMP GET request to retrieve the value associated with an OID.

    :param oid: The OID to retrieve.
    :param host: The hostname or IP address of the device.
    :param port: The port number of the SNMP service on the device.
    :param community: The community string for SNMP authentication.
    :return: The retrieved value or an error message.
    """
    errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
        SnmpEngine(),
        CommunityData(community),
        UdpTransportTarget((host, port)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )

    if errorIndication:
        return str(errorIndication)
    elif errorStatus:
        return '%s at %s' % (
            errorStatus.prettyPrint(),
            errorIndex and varBinds[int(errorIndex)-1][0] or '?'
        )
    else:
        # Assuming only one varBind is returned
        varBind = varBinds[0]
        oid, value = varBind

        # Determining the type and converting the value
        if isinstance(value, (rfc1902.Integer, rfc1902.Integer32)):
            converted_value = int(value)
        elif isinstance(value, (rfc1902.Gauge32, rfc1902.Counter32, rfc1902.Counter64, rfc1902.Unsigned32, rfc1902.TimeTicks)):
            converted_value = float(value)
        else:
            converted_value = value.prettyPrint()  # default to string if type is unknown

        return {
            "type": value.__class__.__name__,
            "value": converted_value
        }