import time

from rpi_utils.display import DisplayHandler


if __name__ == "__main__":
    display_handler = DisplayHandler()
    try:
        while True:
            display_handler.update()

            time.sleep(1)
    except KeyboardInterrupt:
        pass
