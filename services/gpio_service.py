"""
GPIO Service Module
Handles physical button and sensor inputs via Raspberry Pi GPIO pins
Features:
- Reverse signal detection (GPIO 17, voltage divider)
- Button input mapping (pause, skip, volume, etc)
- Non-blocking polling
- Graceful degradation if GPIO unavailable
"""

import logging
import threading
import time
from typing import Callable, Dict, Optional, List
from enum import Enum

# Try to import RPi.GPIO, gracefully handle if not available
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO not available - GPIO functionality disabled")

logger = logging.getLogger(__name__)


class GPIOPin(Enum):
    """GPIO pin definitions for T1000 hardware"""
    REVERSE_SIGNAL = 17  # Voltage divider: 12V reverse → 3.3V GPIO 17
    PAUSE_PLAY = 22
    SKIP_FORWARD = 23
    SKIP_BACK = 24
    VOLUME_UP = 25
    VOLUME_DOWN = 26
    HOME_BUTTON = 27
    CAMERA_SKIP = 4
    RECORD = 5
    POWER = 6
    BRIGHTNESS_UP = 12
    BRIGHTNESS_DOWN = 13


class GPIOService:
    """
    GPIO Input Service
    Monitors physical buttons and sensors
    Provides callbacks for UI screen transitions
    """

    def __init__(self, use_gpio: bool = False, gpio_mode: str = 'BCM'):
        """
        Initialize GPIO service

        Args:
            use_gpio: Enable actual GPIO (False for bench testing)
            gpio_mode: 'BCM' or 'BOARD' numbering scheme
        """
        self.use_gpio = use_gpio and GPIO_AVAILABLE
        self.gpio_mode = gpio_mode
        self.is_running = False
        self.thread = None

        # Button state tracking (debounce)
        self.button_states: Dict[GPIOPin, bool] = {}
        self.last_press_time: Dict[GPIOPin, float] = {}
        self.debounce_ms = 50

        # Reverse signal state
        self.reverse_active = False
        self.reverse_callback: Optional[Callable] = None

        # Button callbacks
        self.button_callbacks: Dict[GPIOPin, List[Callable]] = {}

        if self.use_gpio:
            self._setup_gpio()
        else:
            logger.info("GPIO disabled - bench testing mode (keyboard simulation)")

        logger.info(f"GPIOService initialized (use_gpio={self.use_gpio})")

    def _setup_gpio(self):
        """Configure GPIO pins"""
        if not self.use_gpio:
            return

        try:
            GPIO.setmode(GPIO.BCM if self.gpio_mode == 'BCM' else GPIO.BOARD)
            GPIO.setwarnings(False)

            # Setup reverse signal input with pull-down
            GPIO.setup(GPIOPin.REVERSE_SIGNAL.value, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            logger.info(f"GPIO {GPIOPin.REVERSE_SIGNAL.value} configured for reverse signal")

            # Setup button inputs with pull-up
            button_pins = [
                GPIOPin.PAUSE_PLAY,
                GPIOPin.SKIP_FORWARD,
                GPIOPin.SKIP_BACK,
                GPIOPin.VOLUME_UP,
                GPIOPin.VOLUME_DOWN,
                GPIOPin.HOME_BUTTON,
                GPIOPin.CAMERA_SKIP,
                GPIOPin.RECORD,
                GPIOPin.POWER,
                GPIOPin.BRIGHTNESS_UP,
                GPIOPin.BRIGHTNESS_DOWN,
            ]

            for pin in button_pins:
                GPIO.setup(pin.value, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self.button_states[pin] = False  # Button not pressed
                self.last_press_time[pin] = 0

            logger.info(f"GPIO configured for {len(button_pins)} buttons")

        except Exception as e:
            logger.error(f"GPIO setup failed: {e}")
            self.use_gpio = False

    def register_callback(self, pin: GPIOPin, callback: Callable):
        """
        Register a callback function for button press

        Args:
            pin: GPIO pin
            callback: Function to call on button press (no arguments)
        """
        if pin not in self.button_callbacks:
            self.button_callbacks[pin] = []
        self.button_callbacks[pin].append(callback)
        logger.debug(f"Registered callback for {pin.name}")

    def register_reverse_callback(self, callback: Callable):
        """
        Register callback for reverse signal detection

        Args:
            callback: Function to call when reverse activated (receives bool)
        """
        self.reverse_callback = callback
        logger.debug("Registered reverse signal callback")

    def start(self):
        """Start GPIO polling thread"""
        if self.is_running:
            logger.warning("GPIOService already running")
            return

        logger.info("Starting GPIO polling thread")
        self.is_running = True
        self.thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop GPIO polling and cleanup"""
        logger.info("Stopping GPIO service")
        self.is_running = False

        if self.thread:
            self.thread.join(timeout=5)

        if self.use_gpio:
            try:
                GPIO.cleanup()
                logger.info("GPIO cleaned up")
            except Exception as e:
                logger.warning(f"Error during GPIO cleanup: {e}")

    def _polling_loop(self):
        """Background thread: continuously poll GPIO inputs"""
        polling_interval = 0.02  # 20ms polling (50 Hz)

        while self.is_running:
            try:
                if self.use_gpio:
                    self._check_reverse_signal()
                    self._check_buttons()

                time.sleep(polling_interval)

            except Exception as e:
                logger.error(f"Error in GPIO polling loop: {e}")
                time.sleep(0.1)

    def _check_reverse_signal(self):
        """Check reverse signal input (GPIO 17)"""
        if not self.use_gpio:
            return

        try:
            pin_value = GPIO.input(GPIOPin.REVERSE_SIGNAL.value)

            # Reverse signal active if GPIO 17 reads HIGH (3.3V from voltage divider)
            reverse_now = pin_value == GPIO.HIGH

            if reverse_now != self.reverse_active:
                self.reverse_active = reverse_now
                logger.info(f"Reverse signal {'activated' if reverse_now else 'deactivated'}")

                # Trigger callback
                if self.reverse_callback:
                    try:
                        self.reverse_callback(reverse_now)
                    except Exception as e:
                        logger.error(f"Error in reverse callback: {e}")

        except Exception as e:
            logger.warning(f"Error reading reverse signal: {e}")

    def _check_buttons(self):
        """Check button inputs and trigger callbacks"""
        if not self.use_gpio:
            return

        current_time = time.time() * 1000  # Convert to milliseconds

        for pin in self.button_states.keys():
            try:
                # Read button state (LOW when pressed due to pull-up)
                pin_value = GPIO.input(pin.value)
                button_pressed = pin_value == GPIO.LOW

                # Check debounce
                time_since_last = current_time - self.last_press_time.get(pin, 0)

                if button_pressed and not self.button_states[pin] and time_since_last > self.debounce_ms:
                    # Button transition: not pressed → pressed
                    self.button_states[pin] = True
                    self.last_press_time[pin] = current_time

                    logger.debug(f"Button pressed: {pin.name}")

                    # Trigger callbacks
                    if pin in self.button_callbacks:
                        for callback in self.button_callbacks[pin]:
                            try:
                                callback()
                            except Exception as e:
                                logger.error(f"Error in button callback: {e}")

                elif not button_pressed and self.button_states[pin]:
                    # Button transition: pressed → not pressed
                    self.button_states[pin] = False
                    self.last_press_time[pin] = current_time

            except Exception as e:
                logger.warning(f"Error reading {pin.name}: {e}")

    def simulate_button_press(self, pin: GPIOPin):
        """
        Simulate button press (for bench testing with keyboard)
        Triggers all registered callbacks for the button

        Args:
            pin: GPIO pin to simulate
        """
        logger.debug(f"Simulating button press: {pin.name}")

        if pin in self.button_callbacks:
            for callback in self.button_callbacks[pin]:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in simulated button callback: {e}")

    def simulate_reverse_signal(self, active: bool):
        """
        Simulate reverse signal (for bench testing)

        Args:
            active: True if reverse is active
        """
        logger.debug(f"Simulating reverse signal: {active}")
        self.reverse_active = active

        if self.reverse_callback:
            try:
                self.reverse_callback(active)
            except Exception as e:
                logger.error(f"Error in simulated reverse callback: {e}")

    def get_status(self) -> dict:
        """Get GPIO service status"""
        return {
            'gpio_enabled': self.use_gpio,
            'gpio_available': GPIO_AVAILABLE,
            'polling_active': self.is_running,
            'reverse_signal_active': self.reverse_active,
            'registered_buttons': len(self.button_callbacks),
        }


if __name__ == '__main__':
    # Test GPIO service
    logging.basicConfig(level=logging.DEBUG)

    gpio_service = GPIOService(use_gpio=False)  # Bench test mode
    gpio_service.start()

    # Register some callbacks
    def on_pause():
        print("Pause/Play button pressed!")

    def on_reverse(active):
        print(f"Reverse signal: {active}")

    gpio_service.register_callback(GPIOPin.PAUSE_PLAY, on_pause)
    gpio_service.register_reverse_callback(on_reverse)

    # Simulate button press
    time.sleep(2)
    gpio_service.simulate_button_press(GPIOPin.PAUSE_PLAY)
    gpio_service.simulate_reverse_signal(True)

    time.sleep(2)
    gpio_service.stop()
