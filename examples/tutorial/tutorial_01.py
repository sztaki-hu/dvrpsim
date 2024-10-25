def setup_dvrpsim_import():
    import sys, pathlib, importlib.util

    if importlib.util.find_spec( 'dvrpsim' ) is None:
        source_path = str( pathlib.Path(__file__).resolve().parents[2] / 'src' )
        
        if source_path not in sys.path:
            sys.path.insert(0, source_path)
            
        print( f'module "dvrpsim" will be imported from "{source_path}"' )

setup_dvrpsim_import()

from dvrpsim import Model

class DemoModel(Model):
    def __init__(self) -> None:
        super().__init__()

if __name__ == '__main__':
    model = DemoModel()

    model.run()
