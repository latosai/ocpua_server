import logging
import asyncio
import sys
import numpy as np
import datetime as dt
import copy

sys.path.insert(0, "..")

from asyncua import ua, Server
from asyncua.common.methods import uamethod

@uamethod
def func(parent, value):
    return value * 2


async def write_to_variables(server):
    # random variables
    for n in range(10):
        node = 'ns=2;i=20001'+str(n)
        var = server.get_node(node)
        await var.set_value(np.random.randn(1)[0], ua.VariantType.Float)

    # sinusoidal
    now = dt.datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_today = (now - today).total_seconds()

    periods = [30, 60, 600, 3600, 86400]
    for n in range(5):
        node = 'ns=2;i=20002'+str(n)
        var = server.get_node(node)
        value = np.sin(2 * seconds_today * np.pi / periods[n])
        await var.set_value(value, ua.VariantType.Float)
        
    # random int
    for n in range(5):
        node = 'ns=2;i=20003'+str(n)
        var = server.get_node(node)
        await var.set_value(np.random.randint(100, size=1)[0], ua.VariantType.Int16)                

    # random event
    prob = [10, 20, 50, 100, 1000]
    for n in range(5):
        node = 'ns=2;i=20004'+ str(n)
        var = server.get_node(node)
        event = np.random.rand(1)[0] < 1 / prob[n]
        await var.set_value(event, ua.VariantType.Int16)
        
        
    # random vibration
    lim_max = 2000
    n_hours = 3 # mean time to go from 0 to lim_max
    rate = [1, 0.5, 0.4, 0.9, 0.2, 1, 0.1, 1, 0.7, 0.6]

    for n in range(10):
        node = 'ns=2;i=20005' + str(n)
        var = server.get_node(node)
        
        base_value = await var.read_value()
        base_value = copy.copy(base_value) / lim_max
        
        value = base_value + np.random.rand(1)[0] * 2 / (n_hours * 60 * 60) * rate[n]
                    
        if n == 0:
            if base_value > 0.9:
                reset = True
            else:
                reset = False
                
        if reset:
            value = np.random.rand(1)[0] * 0.2
            
        if value > 1:
            value = 1
            
        await var.set_value(value * lim_max, ua.VariantType.Float)

        
async def main():
    _logger = logging.getLogger('asyncua')
    # setup our server
    server = Server()
    await server.init()

    # # setup our own namespace, not really necessary but should as spec
    server.set_endpoint('opc.tcp://0.0.0.0:4840/freeopcua/server/')
    server.set_server_name('OPC-UA Latos')
    
    await server.import_xml('model/model.xml')


    server.set_security_policy([
            ua.SecurityPolicyType.NoSecurity,
            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256Sha256_Sign])
        
    # idx = await server.get_namespace_index("urn:freeopcua:python:server")

    # setup our own namespace
    uri = "http://examples.freeopcua.github.io"
    # idx = await server.register_namespace(uri)
    
    # dev = await server.nodes.objects.add_object(idx, 'Simulator')
    
    
    _logger.info('Starting server!')
    async with server:
        while True:
            await asyncio.sleep(1)
            
            async_write = asyncio.create_task(write_to_variables(server))
            await async_write                         
            async_write.cancel()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)
    