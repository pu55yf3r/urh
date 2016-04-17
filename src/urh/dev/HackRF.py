from urh.dev.Device import Device
from urh.cythonext import hackrf
import numpy as np
from urh.util.Logger import logger


class HackRF(Device):
    BYTES_PER_SAMPLE = 2  # HackRF device produces 8 bit unsigned IQ data

    def __init__(self, bw, freq, gain, srate, initial_bufsize=8e9, is_ringbuffer=False):
        super().__init__(bw, freq, gain, srate, initial_bufsize, is_ringbuffer)
        self.is_open = False
        self.success = 0

        self.__lut = np.empty(0xffff + 1, dtype=np.complex64)
        self.little_endian = True
        for i in range(0, 0xffff + 1):
            if self.little_endian:
                real = (float(np.int8(i & 0xff))) * (1.0 / 128.0)
                imag = (float(np.int8(i >> 8))) * (1.0 / 128.0)
            else:
                real = (float(np.int8(i >> 8))) * (1.0 / 128.0)
                imag = (float(np.int8(i & 0xff))) * (1.0 / 128.0)

            self.__lut[i] = complex(real, imag)

    def open(self):
        if not self.is_open:
            if hackrf.setup() == self.success:
                self.is_open = True
                logger.info("successfully opened HackRF")
            else:
                logger.warning("failed to open HackRF")

    def close(self):
        if self.is_open:
            if hackrf.exit() == self.success:
                logger.info("successfully closed HackRF")
                self.is_open = False

    def start_rx_mode(self):
        if self.is_open:
            self.set_device_parameters()
            if hackrf.start_rx_mode(self.callback_recv) == self.success:
                logger.info("successfully started HackRF rx mode")
            else:
                logger.error("could not start HackRF rx mode")

    def stop_rx_mode(self, msg):
        if self.is_open:
            logger.info("Stopping rx mode")
            if hackrf.stop_rx_mode() == self.success:
                logger.info("stopped HackRF rx mode (" + str(msg) + ")")
            else:
                logger.error("could not stop HackRF rx mode")

    def set_device_bandwidth(self, bw):
        if self.is_open:

            if hackrf.set_baseband_filter_bandwidth(bw) == self.success:
                logger.info("successfully set HackRF bandwidth to {0}".format(bw))
            else:
                logger.error("failed to set HackRF bandwidth to {0}".format(bw))

    def set_device_frequency(self, value):
        if self.is_open:
            if hackrf.set_freq(value) == self.success:
                logger.info("successfully set HackRF frequency to {0}".format(value))
            else:
                logger.error("failed to set HackRF frequency to {0}".format(value))

    def set_device_gain(self, gain):
        if self.is_open:
            hackrf.set_lna_gain(gain)
            hackrf.set_vga_gain(gain)
            hackrf.set_txvga_gain(gain)

    def set_device_sample_rate(self, sample_rate):
        if self.is_open:
            if hackrf.set_sample_rate(sample_rate) == self.success:
                logger.info("successfully set HackRF sample rate to {0}".format(sample_rate))
            else:
                logger.error("failed to set HackRF sample rate to {0}".format(sample_rate))

    def unpack_complex(self, nvalues: int):
        result = np.empty(nvalues, dtype=np.complex64)
        buffer = self.byte_buffer[:nvalues * self.BYTES_PER_SAMPLE]
        unpacked = np.frombuffer(buffer, dtype=np.uint16)
        for i in range(len(result)):
            result[i] = self.__lut[unpacked[i]]
        return result
