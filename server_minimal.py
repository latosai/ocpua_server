import sys

sys.path.insert(0, "..")
import time
import numpy as np
from opcua import ua, Server
import datetime as dt


if __name__ == "__main__":
    # setup our server
    server = Server()
    server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = server.register_namespace(uri)

    device = server.nodes.objects.add_object(idx, "Simulator")
    name = device.add_variable(idx, "serialNumber", "test")
    name.set_writable()

    variables = {}

    # random variables
    n_variables = 10
    variables['random'] = {}
    random_variables = device.add_object(idx, "RandomVariables")
    for n_variable in range(n_variables):
        var_name = 'random_' + str(n_variable)
        variables['random'][var_name] = random_variables.add_variable(idx, var_name, 0)

    # random cumulate
    n_variables = 10
    variables['random_cumulate'] = {}
    random_variables = device.add_object(idx, "RandomCumulateVariables")
    for n_variable in range(n_variables):
        var_name = 'random_cumulate' + str(n_variable)
        variables['random'][var_name] = random_variables.add_variable(idx, var_name, 0)
    
    # periodic variables
    variables['periodic'] = {}
    periodic_variables = device.add_object(idx, "PeriodicVariables")
    variables['periodic']['sin'] = periodic_variables.add_variable(idx, 'sin', 0)
    variables['periodic']['step'] = periodic_variables.add_variable(idx, 'step', 0)

    # starting!
    server.start()

    try:
        count = 0
        while True:
            time.sleep(1)

            # random variables
            for variable in variables['random'].values():
                variable.set_value(np.random.randn(1)[0])
                
    
            # random cumulate
            for variable in variables['random_cumulate'].values():
                old = variable.get_value()
                variable.set_value(np.random.randn(1)[0] + old)


            # periodic
            sec = dt.datetime.now().second
            sin_value = np.sin(sec * np.pi / 30)
            variables['periodic']['sin'].set_value(sin_value)
            variables['periodic']['step'].set_value(np.sign(sin_value))

    finally:
        # close connection, remove subcsriptions, etc
        server.stop()