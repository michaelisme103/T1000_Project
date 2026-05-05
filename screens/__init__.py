"""
Screens package — T1000 Infotainment System
All Kivy screens with service injection.
"""

from screens.home_screen        import HomeScreen
from screens.camera_screen      import CameraScreen
from screens.music_screen       import MusicScreen
from screens.diagnostics_screen import DiagnosticsScreen
from screens.navigation_screen  import NavigationScreen
from screens.settings_screen    import SettingsScreen
from screens.health_screen      import HealthScreen
from screens.mileage_screen     import MileageScreen

__all__ = [
    'HomeScreen',
    'CameraScreen',
    'MusicScreen',
    'DiagnosticsScreen',
    'NavigationScreen',
    'SettingsScreen',
    'HealthScreen',
    'MileageScreen',
]
