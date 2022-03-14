import subprocess
import time
from typing import List

import psutil
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL.ImageDraw import ImageDraw

from rpi_utils.deluge import DelugeHandler


class DisplayHandler:
    I2C_PORT = 1
    I2C_ADDRESS = 0x3C

    def __init__(self) -> None:
        self.deluge_handler = DelugeHandler()
        self.device = sh1106(i2c(port=DisplayHandler.I2C_PORT, address=DisplayHandler.I2C_ADDRESS))

        self.frame_cntr = 0
        self.display_cntr = 0

    def update(self) -> None:
        if self.frame_cntr % 5 == 0:
            self.display_cntr += 1

        with canvas(self.device) as display:
            self.clear_display(display)

            if self.display_cntr % 2 == 1:
                self.draw_general_stats(display)
            else:
                self.draw_deluge_stats(display)

        self.frame_cntr += 1

    def clear_display(self, display: ImageDraw) -> None:
        display.rectangle(self.device.bounding_box, fill="black")

    def draw_general_stats(self, display: ImageDraw) -> None:
        stats = [
            '       GENERAL:',
            '',
            DisplayHandler.get_ip_message(),
            DisplayHandler.get_cpu_message(),
            DisplayHandler.get_mem_message(),
            DisplayHandler.get_temperature_message(),
            DisplayHandler.get_uptime_message(),
        ]

        self.position_stats_on_display(stats, display)

    def draw_deluge_stats(self, display: ImageDraw) -> None:
        deluge_stats = self.deluge_handler.get_stats()

        stats = [
            '       DELUGE:',
            '',
            f'Up({deluge_stats["seeding"]}): {deluge_stats["upload_speed_bps"]/1024.0:.2f}kBps',
            f'Down({deluge_stats["downloading"]}): {deluge_stats["download_speed_bps"]/1024.0:.2f}kBps'
        ]

        self.position_stats_on_display(stats, display)

    def position_stats_on_display(self, stats: List[str], display: ImageDraw) -> None:
        for idx, stat in enumerate(stats):
            display.text((0, 8 * idx), f"{stat}", fill="white")

    @staticmethod
    def get_ip_message() -> str:
        return DisplayHandler.run_shell_command("hostname -I | cut -d' ' -f1 | awk '{printf \"IP: %s\", $1}'")

    @staticmethod
    def get_cpu_message() -> str:
        return f'Cpu: {psutil.cpu_percent()}%'

    @staticmethod
    def get_mem_message() -> str:
        return f'Mem: {psutil.virtual_memory().percent:.1f}%'

    @staticmethod
    def get_temperature_message() -> str:
        return f'Temp: {psutil.sensors_temperatures(fahrenheit=False)["cpu_thermal"][0].current:.1f}°C'

    @staticmethod
    def get_uptime_message() -> str:
        elapsed_time_since_boot = int(time.time() - psutil.boot_time())

        if elapsed_time_since_boot > 86400:
            days = elapsed_time_since_boot//86400
            time_string = time.strftime("%H:%M:%S", time.gmtime((elapsed_time_since_boot - (86400*days))))

        return f'Up: {days}days, {time_string}'

    @staticmethod
    def run_shell_command(cmd: str) -> str:
        return subprocess.check_output(cmd, shell=True).decode("utf-8")
