
# Driver

https://github.com/QCoDeS/Qcodes/blob/c2ea8d699b65536aadeaf72b5418e2c3ec4896fc/qcodes/instrument_drivers/american_magnetics/AMI430.py

https://github.com/QCoDeS/Qcodes/blob/c2ea8d699b65536aadeaf72b5418e2c3ec4896fc/qcodes/instrument_drivers/american_magnetics/AMI430_visa.py

```
class AMI430(IPInstrument):
    """
    Driver for the American Magnetics Model 430 magnet power supply programmer.

    This class controls a single magnet power supply. In order to use two or
    three magnets simultaneously to set field vectors, first instantiate the
    individual magnets using this class and then pass them as arguments to
    either the AMI430_2D or AMI430_3D virtual instrument classes.

...

class AMI430_3D(Instrument):
    def __init__(self,
                 name: str,
                 instrument_x: Union[AMI430, str],
                 instrument_y: Union[AMI430, str],
                 instrument_z: Union[AMI430, str],
```

# Mocking af AMI430

https://github.com/QCoDeS/Qcodes/blob/6dba5b4319e4b6fc54f2f44d012e88333bf961c3/docs/examples/logging/logging_example.ipynb

https://github.com/QCoDeS/Qcodes/blob/60b7c863c223ddb967502767b984883a8b9e2e55/qcodes/tests/test_logger.py
```
@pytest.fixture()
def AMI430_3D():
```

https://github.com/QCoDeS/Qcodes/blob/5fd7fe96020ca951b61ccd248f0c2aea9dcf5c30/qcodes/tests/drivers/test_ami430_visa.py

# Tests
https://github.com/QCoDeS/Qcodes/blob/69236fb4a8be39f8782edf29678b08aa18354723/docs/examples/driver_examples/Qcodes%20example%20with%20AMI430.ipynb
