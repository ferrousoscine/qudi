"""
A hardware module for acessing the Measurement Systems TSYS01 temperature
sensor chip via SPI.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

import struct
import time

import spidev

from core.configoption import ConfigOption
from core.module import Base
from core.util.mutex import Mutex
from interface.process_interface import ProcessInterface


class TSYS01SPI(Base, ProcessInterface):
    """Measurement Systems TSYS01 temperature sensor.

    Example config for copy-paste:

    temp_tsys:
        module.Class: 'tsys01_spi.TSYS01SPI'
        bus: 0
        device: 0

    """

    # config opts
    bus = ConfigOption("bus", default=0, missing="warn")
    device = ConfigOption("device", default=0, missing="warn")

    # commands to chip (constants)
    READ_ADC = 0x00
    RESET = 0x1E
    START_ADC = 0x48
    READ_ROM0 = 0xA0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # locking for thread safety
        self.threadlock = Mutex()

    def on_activate(self):
        """Activate module."""
        self.rom = []
        self.spi = spidev.SpiDev()
        self.spi.open(self.bus, self.device)
        self.reset()
        self.readROM()

    def on_deactivate(self):
        """Deactivate module."""
        self.spi.close()

    def diag(self):
        """SPI bus diagnostic output."""
        print("==== SPI Diagnostics ====")
        print(f"Bits per word: {self.spi.bits_per_word:>10}")
        print(f"CS is active high: {self.spi.cshigh!s:>6}")
        print(f"Loopback: {self.spi.loop!s:>15}")
        print(f"LSB first: {self.spi.lsbfirst!s:>14}")
        print(f"Max clock speed: {self.spi.max_speed_hz:>8}")
        print(f"Clock mode: {self.spi.mode:>13}")
        print(f"SI/SO shared: {self.spi.threewire!s:>11}")
        print("=========================")

    def reset(self):
        """Reset the sensor chip."""
        rbuf = self.spi.xfer([self.RESET], 8000, 3000)
        time.sleep(0.003)

    def readRomAddr(self, addr):
        """Read a 16bit rom address.

        @param int addr: momory address to read
        @return int: 16bit contents of rom at address
        """
        bytes_to_read = self.READ_ROM0 | 0x0F & (addr << 1)
        rbuf = self.spi.xfer([bytes_to_read, 0x00, 0x00])
        return 2**8 * rbuf[1] + rbuf[2]

    def readROM(self):
        """Read the whole device ROM.

        @return list(int): contents of all 8 ROM registers
        """
        self.rom = []
        for i in range(8):
            self.rom.append(self.readRomAddr(i))

    def startADC(self):
        """Start the temperature sensor ADC."""
        try:
            rbuf = self.spi.xfer([self.START_ADC])
        except OSError:
            pass
        time.sleep(0.010)

    def readADC(self):
        """Read value from the ADC.

        @return int: raw ADC value
        """
        rbuf = self.spi.xfer([self.READ_ADC, 0x00, 0x00, 0x00])
        return struct.unpack(">I", b"\0" + bytes(rbuf[1:]))[0]

    def temperatureCelsius(self, adcValue):
        """Convert ADC value to degrees Celsius.

        @param int adcValue: raw ADC value

        @return float: temperature in degrees Celsius
        """
        if len(self.rom) < 8:
            self.readROM()
        adc16 = adcValue / 2**8
        return (
            -2.0 * self.rom[1] * 10**-21 * adc16**4
            + 4.0 * self.rom[2] * 10**-16 * adc16**3
            + -2.0 * self.rom[3] * 10**-11 * adc16**2
            + 1.0 * self.rom[4] * 10**-6 * adc16
            + -1.5 * self.rom[5] * 10**-2
        )

    def temperatureKelvin(self, adcValue):
        """Convert ADC value to Kelvin.

        @param int adcValue: raw ADC value

        @return float: temperature in Kelvin
        """
        return 273.15 + self.temperatureCelsius(adcValue)

    def get_process_value(self):
        """Read ADC and return emperature in Kelvin.

        @return float: current temperature in Kelvin
        """
        with self.threadlock:
            self.startADC()
            return self.temperatureKelvin(self.readADC())

    def get_process_unit(self):
        """Return Process unit, here Kelvin.

        @return tuple(str, str): short and text form of process unit
        """
        return "K", "kelvin"
