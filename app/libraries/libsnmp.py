import asyncio
from pysnmp.hlapi.asyncio import getCmd, CommunityData, UdpTransportTarget, ObjectType, ObjectIdentity, ContextData, SnmpEngine

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
        for varBind in varBinds:
            return '%s = %s' % (
                varBind[0].prettyPrint(),
                varBind[1].prettyPrint()
            )