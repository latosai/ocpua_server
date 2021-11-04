import logging
import asyncio
import json
import random
from math import e
import sys
import numpy as np
import datetime as dt
import copy

sys.path.insert(0, "..")

from asyncua import ua, Server, Node
from asyncua.common.methods import uamethod


logging.basicConfig(level=logging.INFO, format='%(asctime)-15s (Line %(lineno)d) -> %(message)s')
_logger = logging.getLogger('asyncua')


functions_json = json.loads(open('model/functions.json', 'r').read())
server = None

@uamethod
async def set_random_float_value(parent):
    value = np.random.randn(1)[0]
    return value

@uamethod
async def set_random_int_value(parent):
    value = np.random.randint(100, size=1)[0]
    return value

@uamethod
async def calculate_sinusoidal(parent):
    periods = [30, 60, 600, 3600, 86400]
    identifier = str(parent.Identifier)
    period = periods[int(identifier[-1])]
    now = dt.datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_today = (now - today).total_seconds()
    value = np.sin(2 * seconds_today * np.pi / period)
    return value

@uamethod
async def random_event(parent):
    prob = [10, 20, 50, 100, 1000]
    event = np.random.rand(1)[0] < 1 / random.choice(prob)
    return event

@uamethod
async def random_vibration(parent):
    lim_max = 2000
    n_hours = 3 # mean time to go from 0 to lim_max
    rate = [1, 0.5, 0.4, 0.9, 0.2, 1, 0.1, 1, 0.7, 0.6]

    base_value = await server.get_node(parent).get_value()
    base_value = copy.copy(base_value) / lim_max
    choice = random.choice(rate)
    value = base_value + np.random.rand(1)[0] * 2 / (n_hours * 60 * 60) * choice
    
    reset = False
    if choice == rate[0]:
        if base_value > 0.9:
            reset = True
        else:
            reset = False
                
    if reset:
        value = np.random.rand(1)[0] * 0.2
        
    if value > 1:
        value = 1

    return value

class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    """

    def datachange_notification(self, node, val, data):
        _logger.info(f'Python: New data change event {node}, {val}')

    def event_notification(self, event):
        _logger.info(f"Python: New event {event}")


async def write_to_variables(server, idx):
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

async def apply_function_to_variable(variable_node, idx):
    node_id = variable_node.nodeid
    i = node_id.Identifier
    ns = node_id.NamespaceIndex

    function_name = functions_json.get(f'{ns}:{i}')
    function_name = globals()[function_name]
    datatype = await variable_node.read_data_type_as_variant_type()
    method = await variable_node.add_method(
        idx,
        'myAction',
        function_name,
        [],
        [datatype]
    )
    return True

async def run_function(variable_node, idx):
    node_id = variable_node.nodeid
    i = node_id.Identifier
    ns = node_id.NamespaceIndex
    datatype = await variable_node.read_data_type_as_variant_type()
    result = await variable_node.call_method(f'{ns}:myAction')
    await variable_node.set_value(result, datatype)
    return result


async def subscribe(server, nodes_from_xml):
    handler = SubHandler()
    sub = await server.create_subscription(1000, handler)
    node_objects = []
    for node_id in nodes_from_xml:
        node_obj: Node = server.get_node(node_id)
        try:
            await sub.subscribe_data_change(node_obj)
            node_objects.append(node_obj)
        except:
            _logger.error(f'error subscribing to {node_obj}')
    return handler, sub, node_objects

async def main():
    # setup our server
    global server
    server = Server()
    await server.init()

    # # setup our own namespace, not really necessary but should as spec
    server.set_endpoint('opc.tcp://0.0.0.0:4840/freeopcua/server/')
    server.set_server_name('OPC-UA Latos')
    
    nodes_from_xml = await server.import_xml('model/model.xml')

    ## subscribes to node changes
    handler, subscription, node_objects = await subscribe(server, nodes_from_xml)

    server.set_security_policy([
            ua.SecurityPolicyType.NoSecurity,
            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256Sha256_Sign])
        
    # idx = await server.get_namespace_index("urn:freeopcua:python:server")

    # setup our own namespace
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)
    idx = await server.get_namespace_index(uri)
    # dev = await server.nodes.objects.add_object(idx, 'Simulator')
    
    _logger.info(nodes_from_xml)
    _logger.info('Starting server!')
    async with server:
        objects_with_method = []
        for node in node_objects:
            new_method = await apply_function_to_variable(node, idx)
            if new_method:
                objects_with_method.append(node)
        while True:
            for node in objects_with_method:
                await run_function(node, idx)
            await asyncio.sleep(1)
            
            #async_write = asyncio.create_task(write_to_variables(server, idx))
            #await async_write       
            #async_write.cancel()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)
    