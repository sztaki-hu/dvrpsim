def setup_dvrpsim_import():
    import sys, pathlib, importlib.util

    if importlib.util.find_spec( 'dvrpsim' ) is None:
        source_path = str( pathlib.Path(__file__).resolve().parents[2] / 'src' )
        
        if source_path not in sys.path:
            sys.path.insert(0, source_path)
            
        print( f'module "dvrpsim" will be imported from "{source_path}"' )

setup_dvrpsim_import()

from dvrpsim import Model, Location, Order
from dvrpsim.utils.order_providers import order_provider

class DemoModel(Model):
    def __init__(self) -> None:
        super().__init__()

    # def on_order_request(self, order:Order) -> None:
    #     self.request_for_routing()

if __name__ == '__main__':
    model = DemoModel()

    depot = Location( id= 'DEPOT' )
    model.add_location( depot )

    '''
    for i in range(5):
        customer_location = Location( f'CUSTOMER {i+1}' )
        model.add_location( customer_location )

        order = Order( id= f'O-{i+1}' )
        order.pickup_location = depot
        order.delivery_location = customer_location
        order.release_date = (i+1)*8
        model.request_order( order )
    '''

    orders_to_request = []

    for i in range(5):
        customer_location = Location( id= f'CUSTOMER {i+1}' )
        model.add_location( customer_location )

        order = Order( id= f'O-{i+1}' )
        order.pickup_location = depot
        order.delivery_location = customer_location
        order.release_date = (i+1)*8
        orders_to_request.append( order )

    model.env.process( order_provider( model, orders_to_request, decision_point_on_request= False ) )

    model.run()
