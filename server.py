import logging
import asyncio
import sys
import numpy as np
import datetime as dt

sys.path.insert(0, "..")

from asyncua import ua, Server
from asyncua.common.methods import uamethod



@uamethod
def func(parent, value):
    return value * 2


async def main():
    _logger = logging.getLogger('asyncua')
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://0.0.0.0:4840/freeopcua/server/')

    # setup our own namespace, not really necessary but should as spec
    uri = 'http://examples.freeopcua.github.io'
    idx = await server.register_namespace(uri)

    myobj = await server.nodes.objects.add_object(idx, 'Simulator')
    
    
    variables = {}

    # random variables
    n_variables = 10
    variables['random'] = {}
    random_variables = await myobj.add_object(idx, "RandomVariables")
    for n_variable in range(n_variables):
        var_name = 'Random' + str(n_variable)
        variables['random'][var_name] = await random_variables.add_variable(idx, var_name, 0.1)
    
    # periodic variables
    variables['periodic'] = {}
    periodic_variables = await myobj.add_object(idx, "PeriodicVariables")
    variables['periodic']['Sinusoidal'] = await periodic_variables.add_variable(idx, 'Sinusoidal', 0.1)
   
       
    _logger.info('Starting server!')
    async with server:
        while True:
            await asyncio.sleep(1)
            
            # random variables
            for variable in variables['random'].values():
                await variable.write_value(np.random.randn(1)[0])

            # periodic
            sec = dt.datetime.now().second
            sin_value = np.sin(sec * np.pi / 30)
            await variables['periodic']['Sinusoidal'].write_value(sin_value)
            

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)