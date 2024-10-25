# Our first model

It's time to create our first model!

***

1. First of all, we need to import class ``Model``.
2. Now, we can make our own model class, say ``DemoModel``.
3. Finally, we can create an instance of this class and run it.

```python
from dvrpsim import Model

class DemoModel(Model):
    def __init__(self) -> None:
        super().__init__()

if __name__ == '__main__':
    model = DemoModel()

    model.run()
```

However, do not expect an interesting result...

```txt
    INFO    :        0.0 | 00:00:00 | START
    INFO    :        0.0 | 00:00:00 | FINISH
```

***

So, let's add some orders to the model!
