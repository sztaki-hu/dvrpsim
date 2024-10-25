class ModelError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class SimulationError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class RoutingError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
