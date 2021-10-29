import logging
import asyncio
import sys
sys.path.insert(0, "..")

from asyncua import Server

import numpy as np

n_var = 1000

async def main():
    _logger = logging.getLogger('asyncua')
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://0.0.0.0:4840/freeopcua/server/')

    # setup our own namespace, not really necessary but should as spec
    uri = 'http://examples.freeopcua.github.io'
    idx = await server.register_namespace(uri)

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    
    myobj = await server.nodes.objects.add_object(idx, 'Random')

    # add variables
    var_dict = {}
    for n in range(n_var):
        var_dict['random'+str(n)] = await myobj.add_variable(idx, 'Random'+str(n), 0.1)
   
    _logger.info('Starting server!')
    
    async with server:
        while True:
            await asyncio.sleep(1)
            
            for var_name, var in var_dict.items():
                print(var_name)
                await var.write_value(np.random.randn(1)[0])
                value = await var.get_value()
                print(value)


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)