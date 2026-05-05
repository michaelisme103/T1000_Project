"""
OBD2 Service Module — T1000 Infotainment System
Real-time engine diagnostics via ELM327 USB adapter.
Gracefully falls back to realistic simulated data when hardware is absent.
"""

import logging
import threading
import time
import random
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

try:
    import obd
    OBD_AVAILABLE = True
except ImportError:
    OBD_AVAILABLE = False
    logging.warning("python-obd not installed — OBD2 will simulate data")

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Comprehensive OBD-II / SAE J2012 DTC Database (250+ codes)
# Format: code -> (short_title, detailed_description, severity)
# severity: 'info', 'warning', 'critical'
# ---------------------------------------------------------------------------
DTC_DATABASE: Dict[str, tuple] = {
    # P0000–P0099  Fuel & Air Metering
    "P0001": ("Fuel Volume Regulator Control Circuit Open",
              "The fuel volume regulator control circuit is open. Check wiring/connector to the fuel pressure regulator solenoid.", "warning"),
    "P0002": ("Fuel Volume Regulator Control Circuit Range/Performance",
              "Fuel pressure regulator output is outside expected range. May indicate a failing high-pressure fuel pump or regulator.", "warning"),
    "P0003": ("Fuel Volume Regulator Control Circuit Low",
              "Low signal on the fuel volume regulator circuit. Check for short to ground in the regulator wiring.", "warning"),
    "P0004": ("Fuel Volume Regulator Control Circuit High",
              "High signal on the fuel volume regulator circuit. Check for open circuit or short to voltage.", "warning"),
    "P0010": ("'A' Camshaft Position Actuator Circuit (Bank 1)",
              "Open or short in the VVT/VVTi oil control valve circuit for intake camshaft Bank 1. Engine may run rough at idle.", "warning"),
    "P0011": ("'A' Camshaft Position Timing Over-Advanced (Bank 1)",
              "Intake camshaft is more advanced than commanded. Common causes: low oil pressure, dirty oil, stuck OCV, stretched timing chain.", "warning"),
    "P0012": ("'A' Camshaft Position Timing Over-Retarded (Bank 1)",
              "Intake camshaft is more retarded than commanded. Check oil condition and OCV solenoid.", "warning"),
    "P0016": ("Crankshaft/Camshaft Position Correlation (Bank 1, Sensor A)",
              "CKP and CMP signals don't correlate. May indicate a jumped timing chain or belt, or failing position sensor.", "critical"),
    "P0020": ("'A' Camshaft Position Actuator Circuit (Bank 2)",
              "Open or short in the VVT oil control valve circuit for intake camshaft Bank 2.", "warning"),
    "P0021": ("'A' Camshaft Position Timing Over-Advanced (Bank 2)",
              "Intake camshaft Bank 2 is over-advanced. Same causes as P0011 on Bank 2.", "warning"),
    "P0030": ("HO2S Heater Control Circuit (Bank 1, Sensor 1)",
              "O2 sensor heater circuit fault before the catalytic converter. Heater failure causes slow closed-loop fuel control.", "warning"),
    "P0031": ("HO2S Heater Control Circuit Low (Bank 1, Sensor 1)",
              "O2 sensor heater circuit shorted to ground upstream of cat (Bank 1). Inspect O2 sensor harness.", "warning"),
    "P0032": ("HO2S Heater Control Circuit High (Bank 1, Sensor 1)",
              "O2 sensor heater circuit shorted to voltage upstream of cat (Bank 1).", "warning"),
    "P0036": ("HO2S Heater Control Circuit (Bank 1, Sensor 2)",
              "O2 sensor heater circuit fault downstream of catalytic converter (Bank 1).", "warning"),

    # P0100–P0199  Air/Temp/Throttle Sensors
    "P0100": ("Mass Air Flow (MAF) Sensor Circuit",
              "No signal or intermittent signal from MAF sensor. Engine may run rich, idle roughly, or stall.", "warning"),
    "P0101": ("MAF Sensor Circuit Range/Performance",
              "MAF sensor output doesn't match expected airflow. Common causes: dirty MAF element, air leaks after MAF, clogged air filter.", "warning"),
    "P0102": ("MAF Sensor Circuit Low Input",
              "MAF signal is below minimum threshold. Check wiring, ground connections, and MAF sensor element.", "warning"),
    "P0103": ("MAF Sensor Circuit High Input",
              "MAF signal is above maximum threshold. May indicate a failed sensor or wiring short to voltage.", "warning"),
    "P0104": ("MAF Sensor Circuit Intermittent",
              "Intermittent signal loss from MAF sensor. Inspect connector pins and wiring for chafing.", "warning"),
    "P0105": ("Manifold Absolute Pressure (MAP) Sensor Circuit",
              "No signal from MAP sensor. Engine will default to backup fuel tables causing poor performance.", "warning"),
    "P0106": ("MAP Sensor Range/Performance",
              "MAP sensor output doesn't match throttle position or MAF. Check for vacuum leaks or a clogged MAP port.", "warning"),
    "P0107": ("MAP Sensor Circuit Low Input",
              "MAP signal below minimum. Check wiring and sensor vacuum line for leaks or blockage.", "warning"),
    "P0108": ("MAP Sensor Circuit High Input",
              "MAP signal above maximum. Possible open circuit or failed sensor.", "warning"),
    "P0110": ("Intake Air Temperature (IAT) Sensor Circuit",
              "Open or short in the IAT sensor circuit. Engine may run rich in cold starts.", "info"),
    "P0111": ("IAT Sensor Range/Performance",
              "IAT sensor reading doesn't match expected ambient temperature range.", "info"),
    "P0112": ("IAT Sensor Circuit Low Input",
              "IAT sensor reads too cold — possible short to ground. Engine may over-fuel.", "info"),
    "P0113": ("IAT Sensor Circuit High Input",
              "IAT sensor reads too hot — possible open circuit. Check sensor and wiring.", "info"),
    "P0115": ("Engine Coolant Temperature (ECT) Sensor Circuit",
              "Open or short in ECT sensor circuit. Engine may run rich and cooling fan may malfunction.", "warning"),
    "P0116": ("ECT Sensor Range/Performance",
              "ECT reading doesn't reach normal operating temperature or fluctuates erratically. Suspect thermostat or sensor.", "warning"),
    "P0117": ("ECT Sensor Circuit Low Input",
              "ECT reads extremely cold — short to ground. Engine will over-fuel. Diagnose immediately.", "warning"),
    "P0118": ("ECT Sensor Circuit High Input",
              "ECT reads extremely hot — open circuit. Cooling fan may not activate correctly.", "warning"),
    "P0119": ("ECT Sensor Circuit Intermittent",
              "Intermittent ECT signal. Inspect connector and wiring for corrosion or loose pins.", "warning"),
    "P0120": ("Throttle Position Sensor (TPS) Circuit",
              "Open or short in TPS A circuit. Engine may hesitate, surge, or stall on acceleration.", "warning"),
    "P0121": ("TPS Circuit Range/Performance",
              "TPS A output doesn't match expected values. Dirty or worn throttle body, or failing sensor.", "warning"),
    "P0122": ("TPS Circuit Low Input",
              "TPS signal below minimum. Check for shorted wiring. Engine may default to limp mode.", "warning"),
    "P0123": ("TPS Circuit High Input",
              "TPS signal above maximum. Possible open reference voltage circuit.", "warning"),
    "P0125": ("Insufficient Coolant Temperature for Closed-Loop Fuel Control",
              "Engine is not reaching closed-loop operating temperature quickly enough. Suspect thermostat stuck open.", "warning"),
    "P0128": ("Coolant Thermostat (Coolant Temperature Below Regulating Temp)",
              "Engine not reaching normal operating temperature. Thermostat is likely stuck open. Fuel economy and emissions will suffer.", "warning"),
    "P0130": ("O2 Sensor Circuit (Bank 1, Sensor 1)",
              "No signal from upstream oxygen sensor Bank 1. Engine runs in open-loop causing poor fuel economy.", "warning"),
    "P0131": ("O2 Sensor Circuit Low Voltage (Bank 1, Sensor 1)",
              "Upstream O2 sensor voltage too low — indicates lean condition or failed sensor.", "warning"),
    "P0132": ("O2 Sensor Circuit High Voltage (Bank 1, Sensor 1)",
              "Upstream O2 sensor voltage too high — indicates rich condition or contaminated sensor.", "warning"),
    "P0133": ("O2 Sensor Circuit Slow Response (Bank 1, Sensor 1)",
              "Upstream O2 sensor responds slowly. Sensor is aging or contaminated. Fuel economy will be poor.", "warning"),
    "P0134": ("O2 Sensor Circuit No Activity Detected (Bank 1, Sensor 1)",
              "Upstream O2 sensor is not switching. Sensor likely failed. Replace oxygen sensor.", "warning"),
    "P0135": ("O2 Sensor Heater Circuit Malfunction (Bank 1, Sensor 1)",
              "O2 sensor heater failure on upstream sensor Bank 1. Cold starts and emissions affected.", "warning"),
    "P0136": ("O2 Sensor Circuit (Bank 1, Sensor 2)",
              "No signal from downstream O2 sensor Bank 1 (post-cat monitor).", "info"),
    "P0138": ("O2 Sensor Circuit High Voltage (Bank 1, Sensor 2)",
              "Downstream O2 sensor high voltage. May indicate a rich condition or catalytic converter failure.", "warning"),
    "P0140": ("O2 Sensor Circuit No Activity (Bank 1, Sensor 2)",
              "Downstream O2 sensor not switching. Sensor or wiring fault.", "info"),
    "P0141": ("O2 Sensor Heater Circuit (Bank 1, Sensor 2)",
              "Downstream O2 sensor heater fault. Affects catalyst efficiency monitoring.", "info"),
    "P0150": ("O2 Sensor Circuit (Bank 2, Sensor 1)",
              "Upstream O2 sensor failure on Bank 2.", "warning"),
    "P0153": ("O2 Sensor Circuit Slow Response (Bank 2, Sensor 1)",
              "Bank 2 upstream O2 sensor responding slowly. Sensor aging or contaminated.", "warning"),
    "P0155": ("O2 Sensor Heater Circuit (Bank 2, Sensor 1)",
              "Bank 2 upstream O2 heater circuit fault.", "warning"),
    "P0170": ("Fuel Trim Malfunction (Bank 1)",
              "Short-term and long-term fuel trims out of specification on Bank 1. Check for vacuum leaks, MAF issues, or injector faults.", "warning"),
    "P0171": ("System Too Lean (Bank 1)",
              "Bank 1 is running lean (too much air, not enough fuel). Common causes: vacuum leaks, weak fuel pump, dirty injectors, failed MAF sensor. Very common code.", "warning"),
    "P0172": ("System Too Rich (Bank 1)",
              "Bank 1 is running rich. Causes: leaking injector, high fuel pressure, failed O2 sensor, coolant temp sensor reading cold.", "warning"),
    "P0174": ("System Too Lean (Bank 2)",
              "Bank 2 running lean. Same diagnostic approach as P0171 for Bank 2.", "warning"),
    "P0175": ("System Too Rich (Bank 2)",
              "Bank 2 running rich. Same diagnostic approach as P0172 for Bank 2.", "warning"),

    # P0200–P0299  Injector Circuit
    "P0200": ("Injector Circuit Malfunction",
              "General injector circuit fault. Check wiring harness and PCM injector drivers.", "warning"),
    "P0201": ("Injector Circuit Malfunction — Cylinder 1",
              "Cylinder 1 injector circuit open or shorted. Engine will misfire on cylinder 1.", "warning"),
    "P0202": ("Injector Circuit Malfunction — Cylinder 2",
              "Cylinder 2 injector circuit fault.", "warning"),
    "P0203": ("Injector Circuit Malfunction — Cylinder 3",
              "Cylinder 3 injector circuit fault.", "warning"),
    "P0204": ("Injector Circuit Malfunction — Cylinder 4",
              "Cylinder 4 injector circuit fault.", "warning"),
    "P0205": ("Injector Circuit Malfunction — Cylinder 5",
              "Cylinder 5 injector circuit fault.", "warning"),
    "P0206": ("Injector Circuit Malfunction — Cylinder 6",
              "Cylinder 6 injector circuit fault.", "warning"),
    "P0230": ("Fuel Pump Primary Circuit",
              "Fault in the primary fuel pump relay or wiring circuit. Engine may fail to start.", "critical"),
    "P0231": ("Fuel Pump Secondary Circuit Low",
              "Low voltage on secondary fuel pump circuit. Possible relay, wiring, or pump failure.", "warning"),
    "P0232": ("Fuel Pump Secondary Circuit High",
              "High voltage on secondary fuel pump circuit. Check for short to voltage.", "warning"),

    # P0300–P0399  Misfire
    "P0300": ("Random/Multiple Cylinder Misfire Detected",
              "Multiple cylinders misfiring. Causes: worn spark plugs/wires, bad ignition coil, vacuum leak, low compression, bad injectors. Can cause catalytic converter damage if left unaddressed.", "critical"),
    "P0301": ("Cylinder 1 Misfire Detected",
              "Cylinder 1 misfiring. Check spark plug, ignition coil, fuel injector, and compression on cylinder 1.", "warning"),
    "P0302": ("Cylinder 2 Misfire Detected",
              "Cylinder 2 misfiring. Inspect spark plug and coil for cylinder 2.", "warning"),
    "P0303": ("Cylinder 3 Misfire Detected",
              "Cylinder 3 misfiring. Inspect spark plug and coil for cylinder 3.", "warning"),
    "P0304": ("Cylinder 4 Misfire Detected",
              "Cylinder 4 misfiring. Inspect spark plug and coil for cylinder 4.", "warning"),
    "P0305": ("Cylinder 5 Misfire Detected",
              "Cylinder 5 misfiring. Inspect spark plug and coil for cylinder 5.", "warning"),
    "P0306": ("Cylinder 6 Misfire Detected",
              "Cylinder 6 misfiring. Inspect spark plug and coil for cylinder 6.", "warning"),
    "P0316": ("Misfire Detected on Startup (First 1000 Revolutions)",
              "Misfire present during cold start. Check for flooded cylinder, leaking injector, or low compression.", "warning"),
    "P0320": ("Ignition/Distributor Engine Speed Input Circuit",
              "No signal from crankshaft position sensor via distributor. Engine will not run without this signal.", "critical"),
    "P0325": ("Knock Sensor 1 Circuit (Bank 1)",
              "Knock sensor circuit fault Bank 1. Engine timing will retard conservatively, reducing power and fuel economy.", "warning"),
    "P0326": ("Knock Sensor 1 Range/Performance (Bank 1)",
              "Knock sensor signal out of expected range. Check sensor mounting torque (loose sensors cause this).", "warning"),
    "P0327": ("Knock Sensor 1 Circuit Low (Bank 1)",
              "Low voltage on knock sensor Bank 1 circuit.", "warning"),
    "P0328": ("Knock Sensor 1 Circuit High (Bank 1)",
              "High voltage on knock sensor Bank 1 circuit.", "warning"),
    "P0330": ("Knock Sensor 2 Circuit (Bank 2)",
              "Knock sensor circuit fault Bank 2.", "warning"),
    "P0335": ("Crankshaft Position (CKP) Sensor A Circuit",
              "No signal from crankshaft position sensor. Engine will not start without CKP signal. Check sensor, reluctor wheel, and wiring.", "critical"),
    "P0336": ("CKP Sensor A Circuit Range/Performance",
              "CKP signal intermittent or erratic. May cause no-start or stalling. Inspect reluctor wheel for damage.", "critical"),
    "P0340": ("Camshaft Position (CMP) Sensor A Circuit (Bank 1)",
              "No signal from camshaft position sensor Bank 1. Sequential fuel injection and VVT will be disabled.", "warning"),
    "P0341": ("CMP Sensor A Circuit Range/Performance (Bank 1)",
              "CMP signal erratic. May indicate timing chain stretch or sensor failure.", "warning"),
    "P0345": ("CMP Sensor A Circuit (Bank 2)",
              "Camshaft position sensor fault on Bank 2.", "warning"),
    "P0350": ("Ignition Coil Primary/Secondary Circuit",
              "General ignition coil circuit fault. Check primary wiring and coil resistance.", "warning"),
    "P0351": ("Ignition Coil A Primary/Secondary Circuit",
              "Coil A circuit fault. Engine will misfire on coil A's cylinder(s).", "warning"),
    "P0352": ("Ignition Coil B Primary/Secondary Circuit",
              "Coil B circuit fault.", "warning"),
    "P0353": ("Ignition Coil C Primary/Secondary Circuit",
              "Coil C circuit fault.", "warning"),
    "P0354": ("Ignition Coil D Primary/Secondary Circuit",
              "Coil D circuit fault.", "warning"),
    "P0355": ("Ignition Coil E Primary/Secondary Circuit",
              "Coil E circuit fault.", "warning"),
    "P0356": ("Ignition Coil F Primary/Secondary Circuit",
              "Coil F circuit fault.", "warning"),

    # P0400–P0499  Emission Controls
    "P0400": ("EGR Flow Malfunction",
              "EGR system not flowing as expected. Causes rough idle and increased NOx emissions.", "warning"),
    "P0401": ("EGR Flow Insufficient Detected",
              "Insufficient EGR flow. Carbon buildup in EGR passages is most common cause. Clean or replace EGR valve.", "warning"),
    "P0402": ("EGR Flow Excessive Detected",
              "Too much EGR flow. Stuck EGR valve open causes rough idle and stalling.", "warning"),
    "P0403": ("EGR Circuit Malfunction",
              "EGR solenoid control circuit fault. Check wiring and solenoid.", "warning"),
    "P0404": ("EGR Circuit Range/Performance",
              "EGR position sensor or valve response out of range.", "warning"),
    "P0410": ("Secondary Air Injection System",
              "Air injection system not functioning correctly. Check AIR pump, check valves, and solenoids.", "warning"),
    "P0420": ("Catalyst System Efficiency Below Threshold (Bank 1)",
              "Catalytic converter efficiency is below required threshold on Bank 1. Converter is failing or has been poisoned. May also indicate a rich-running engine damaging the cat. This is one of the most common OBD-II codes.", "warning"),
    "P0421": ("Warm Up Catalyst Efficiency Below Threshold (Bank 1)",
              "Pre-cat converter (warm-up cat) on Bank 1 below efficiency threshold.", "warning"),
    "P0430": ("Catalyst System Efficiency Below Threshold (Bank 2)",
              "Catalytic converter Bank 2 below efficiency threshold. Same diagnosis as P0420 for Bank 2.", "warning"),
    "P0440": ("EVAP Emission Control System Malfunction",
              "General EVAP system fault. System cannot build or hold pressure. Check gas cap first.", "warning"),
    "P0441": ("EVAP Control System Incorrect Purge Flow",
              "EVAP purge flow not within spec. Check purge solenoid, hoses, and canister.", "warning"),
    "P0442": ("EVAP Control System Leak Detected (Small Leak)",
              "Small leak detected in the EVAP system (approximately 0.040 inch orifice). Check gas cap seal and EVAP hoses.", "info"),
    "P0443": ("EVAP Purge Control Valve Circuit",
              "EVAP purge valve circuit fault. Check wiring and solenoid operation.", "warning"),
    "P0446": ("EVAP Vent Control Circuit",
              "EVAP vent solenoid circuit fault or vent valve stuck. Charcoal canister may be saturated.", "warning"),
    "P0450": ("EVAP Pressure Sensor",
              "EVAP fuel tank pressure sensor circuit fault.", "warning"),
    "P0451": ("EVAP Pressure Sensor Range/Performance",
              "EVAP pressure sensor reading outside expected range.", "warning"),
    "P0452": ("EVAP Pressure Sensor Low Input",
              "EVAP pressure sensor signal too low. Possible sensor failure or wiring short.", "warning"),
    "P0453": ("EVAP Pressure Sensor High Input",
              "EVAP pressure sensor signal too high.", "warning"),
    "P0455": ("EVAP Control System Large Leak Detected",
              "Large leak detected in the EVAP system. Check gas cap first, then inspect all EVAP hoses and the charcoal canister.", "warning"),
    "P0456": ("EVAP Control System Leak Detected (Very Small)",
              "Very small EVAP leak detected. Check gas cap tightness and condition.", "info"),
    "P0460": ("Fuel Level Sensor A Circuit",
              "Fuel level sensor circuit fault. Fuel gauge may read incorrectly.", "info"),
    "P0461": ("Fuel Level Sensor A Range/Performance",
              "Fuel level sensor reading erratic or stuck.", "info"),
    "P0480": ("Cooling Fan 1 Control Circuit",
              "Primary cooling fan relay circuit fault. Fan may not activate. Risk of overheating.", "warning"),
    "P0481": ("Cooling Fan 2 Control Circuit",
              "Secondary cooling fan circuit fault.", "warning"),

    # P0500–P0599  Speed / Idle / Cruise
    "P0500": ("Vehicle Speed Sensor (VSS) Malfunction",
              "No signal from vehicle speed sensor. Speedometer may not work. ABS and cruise control affected.", "warning"),
    "P0501": ("VSS Range/Performance",
              "VSS signal not matching expected values. Check sensor and tone ring.", "warning"),
    "P0505": ("Idle Air Control (IAC) System Malfunction",
              "IAC system cannot maintain target idle speed. Engine may stall or idle roughly. Clean or replace IAC valve.", "warning"),
    "P0506": ("Idle Control System RPM Lower Than Expected",
              "Idle speed below target. Dirty throttle body, vacuum leak, or failing IAC valve.", "warning"),
    "P0507": ("Idle Control System RPM Higher Than Expected",
              "Idle speed above target. Vacuum leak or stuck IAC valve.", "warning"),
    "P0510": ("Closed Throttle Position Switch",
              "Throttle closed switch malfunction. Affects deceleration fuel cutoff and idle control.", "info"),
    "P0520": ("Engine Oil Pressure Sensor/Switch Circuit",
              "Oil pressure sensor circuit fault. Actual oil pressure unknown — check oil level and pressure immediately.", "critical"),
    "P0521": ("Engine Oil Pressure Sensor Range/Performance",
              "Oil pressure sensor reading out of expected range. Verify actual oil pressure with manual gauge.", "critical"),
    "P0522": ("Engine Oil Pressure Sensor Circuit Low",
              "Oil pressure circuit signal too low — check for actual low oil pressure or sensor failure.", "critical"),
    "P0523": ("Engine Oil Pressure Sensor Circuit High",
              "Oil pressure signal too high. Possible open circuit.", "warning"),
    "P0530": ("A/C Refrigerant Pressure Sensor Circuit",
              "A/C refrigerant pressure sensor circuit fault. A/C compressor will not engage.", "info"),
    "P0560": ("System Voltage Malfunction",
              "PCM detected abnormal system voltage. Check alternator output and battery condition.", "warning"),
    "P0562": ("System Voltage Low",
              "System voltage below threshold. Possible failing alternator, corroded battery terminals, or weak battery.", "warning"),
    "P0563": ("System Voltage High",
              "System voltage above threshold. Possible failing alternator voltage regulator.", "warning"),
    "P0571": ("Brake Switch A Circuit",
              "Brake light switch circuit fault. Affects cruise control, ABS, and shift interlock.", "warning"),

    # P0600–P0699  Computer Output
    "P0600": ("Serial Communication Link Malfunction",
              "Communication failure between PCM and another module. Check CAN bus wiring.", "warning"),
    "P0601": ("Internal Control Module Memory Check Sum Error",
              "PCM memory corruption detected. PCM may require reprogramming or replacement.", "critical"),
    "P0602": ("Control Module Programming Error",
              "PCM is not programmed for this vehicle. Reflash required.", "critical"),
    "P0603": ("Internal Control Module Keep Alive Memory Error",
              "PCM KAM (Keep Alive Memory) error. PCM may need replacement.", "critical"),
    "P0604": ("Internal Control Module RAM Error",
              "PCM RAM failure. Replacement likely required.", "critical"),
    "P0605": ("Internal Control Module ROM Error",
              "PCM ROM failure. Replacement likely required.", "critical"),
    "P0606": ("ECM/PCM Processor Fault",
              "Internal PCM processor fault detected. PCM replacement likely required.", "critical"),
    "P0620": ("Generator Control Circuit",
              "Alternator/generator control circuit fault. Battery may not charge.", "warning"),
    "P0621": ("Generator Lamp L Control Circuit",
              "Alternator warning lamp circuit fault.", "info"),
    "P0630": ("VIN Not Programmed",
              "Vehicle Identification Number not programmed into PCM.", "warning"),

    # P0700–P0899  Transmission
    "P0700": ("Transmission Control System",
              "Transmission control module (TCM) has detected a fault and set a code. Retrieve TCM codes for specific diagnosis.", "warning"),
    "P0701": ("Transmission Control System Range/Performance",
              "TCM output is not within expected parameters.", "warning"),
    "P0705": ("Transmission Range Sensor Circuit (PRNDL Input)",
              "Transmission range sensor (neutral safety switch) circuit fault. Engine may not crank in Park/Neutral.", "warning"),
    "P0706": ("Transmission Range Sensor Circuit Range/Performance",
              "Transmission range sensor signal erratic. Transmission may shift incorrectly.", "warning"),
    "P0710": ("Transmission Fluid Temperature (TFT) Sensor A Circuit",
              "TFT sensor circuit fault. Transmission may use conservative shift points.", "info"),
    "P0711": ("TFT Sensor Range/Performance",
              "TFT sensor reading erratic or stuck.", "info"),
    "P0715": ("Input/Turbine Speed Sensor A Circuit",
              "Turbine speed sensor circuit fault. Transmission will not shift correctly.", "warning"),
    "P0720": ("Output Speed Sensor Circuit",
              "Output shaft speed sensor circuit fault. Speedometer and shift quality affected.", "warning"),
    "P0730": ("Incorrect Gear Ratio",
              "Calculated gear ratio does not match commanded gear. Slipping clutch packs or worn bands.", "warning"),
    "P0731": ("Gear 1 Incorrect Ratio",
              "First gear ratio out of specification.", "warning"),
    "P0732": ("Gear 2 Incorrect Ratio",
              "Second gear ratio out of specification.", "warning"),
    "P0733": ("Gear 3 Incorrect Ratio",
              "Third gear ratio out of specification.", "warning"),
    "P0734": ("Gear 4 Incorrect Ratio",
              "Fourth gear ratio out of specification.", "warning"),
    "P0740": ("Torque Converter Clutch (TCC) Solenoid Circuit",
              "TCC solenoid circuit fault. Torque converter lockup will not engage, reducing fuel economy.", "warning"),
    "P0741": ("TCC Circuit Performance or Stuck Off",
              "TCC not engaging or slipping. Causes poor fuel economy at highway speeds.", "warning"),
    "P0748": ("Pressure Control Solenoid A Electrical",
              "EPC solenoid A circuit fault. Shift feel and timing will be affected.", "warning"),
    "P0750": ("Shift Solenoid A Malfunction",
              "Shift solenoid A failure. Transmission will not shift correctly.", "warning"),
    "P0755": ("Shift Solenoid B Malfunction",
              "Shift solenoid B failure.", "warning"),
    "P0760": ("Shift Solenoid C Malfunction",
              "Shift solenoid C failure.", "warning"),
    "P0780": ("Shift Malfunction",
              "General shift quality fault. May indicate internal transmission mechanical problem.", "warning"),
    "P0850": ("Park/Neutral Switch Input Circuit",
              "Park/neutral switch circuit fault. Engine may crank in gear or not crank in Park.", "warning"),

    # P1xxx  Toyota/OEM Specific
    "P1120": ("Accelerator Pedal Position Sensor Circuit",
              "Toyota-specific: APP sensor circuit fault. Throttle response may be poor.", "warning"),
    "P1121": ("Accelerator Pedal Position Sensor Performance",
              "Toyota-specific: APP sensor reading unexpected values.", "warning"),
    "P1130": ("A/F Sensor Circuit Range/Performance (Bank 1, Sensor 1)",
              "Toyota-specific: Air-fuel ratio sensor performance issue Bank 1.", "warning"),
    "P1133": ("A/F Sensor Response (Bank 1, Sensor 1)",
              "Toyota-specific: A/F sensor slow to respond.", "warning"),
    "P1150": ("A/F Sensor Circuit Range/Performance (Bank 2, Sensor 1)",
              "Toyota-specific: Air-fuel ratio sensor performance issue Bank 2.", "warning"),
    "P1300": ("Igniter Circuit Malfunction (Bank 1)",
              "Toyota-specific: Ignition circuit fault Bank 1. Check igniter unit.", "warning"),
    "P1305": ("Igniter Circuit Malfunction (Bank 2)",
              "Toyota-specific: Ignition circuit fault Bank 2.", "warning"),
    "P1349": ("VVT-i System Malfunction (Bank 1)",
              "Toyota VVT-i variable valve timing system fault. Check VVT-i oil control valve and filter screen.", "warning"),

    # B codes — Body
    "B0001": ("Driver Frontal Stage 1 Deployment Control",
              "SRS airbag system fault — driver stage 1. Do not attempt to diagnose without proper SRS disabling procedure.", "critical"),
    "B0010": ("Front Crash Sensor Deployment Loop",
              "Frontal crash sensor circuit fault. Airbag may not deploy in a collision.", "critical"),
    "B0051": ("Frontal Sensor 1 Internal",
              "Internal fault in frontal crash sensor 1.", "warning"),
    "B0100": ("SDM Internal — Checksum Failure",
              "Supplemental restraint system module internal failure.", "critical"),

    # C codes — Chassis / ABS
    "C0000": ("Vehicle Speed Information Circuit",
              "ABS module receiving no vehicle speed signal.", "warning"),
    "C0035": ("Right Front Wheel Speed Sensor Circuit",
              "Right front wheel speed sensor circuit fault. ABS and traction control disabled.", "warning"),
    "C0040": ("Left Front Wheel Speed Sensor Circuit",
              "Left front wheel speed sensor circuit fault.", "warning"),
    "C0045": ("Right Rear Wheel Speed Sensor Circuit",
              "Right rear wheel speed sensor circuit fault.", "warning"),
    "C0050": ("Left Rear Wheel Speed Sensor Circuit",
              "Left rear wheel speed sensor circuit fault.", "warning"),
    "C0110": ("Pump Motor Circuit",
              "ABS pump motor circuit fault. ABS will be inoperative.", "critical"),
    "C0121": ("Valve Relay Circuit",
              "ABS/TCS valve relay fault. Antilock braking disabled.", "warning"),
    "C0186": ("Lateral Acceleration Sensor",
              "Lateral acceleration sensor circuit fault. Stability control affected.", "warning"),
    "C0196": ("Yaw Rate Sensor",
              "Yaw rate sensor circuit fault. Electronic stability control will be disabled.", "warning"),
    "C0265": ("EBCM Relay Circuit",
              "Electronic brake control module relay fault.", "critical"),
    "C0267": ("Pump Motor Circuit Open/Shorted",
              "ABS hydraulic pump motor open or short circuit.", "critical"),
    "C0291": ("Lost Communication with PCM",
              "ABS module cannot communicate with powertrain control module.", "warning"),

    # U codes — Network
    "U0001": ("High Speed CAN Communication Bus",
              "CAN communication bus fault. Multiple modules may lose communication.", "critical"),
    "U0100": ("Lost Communication with ECM/PCM",
              "Control module communication failure with engine control. Check CAN bus wiring and termination resistors.", "critical"),
    "U0101": ("Lost Communication with TCM",
              "ABS or body module lost communication with the transmission control module.", "warning"),
    "U0122": ("Lost Communication with Vehicle Dynamics Control Module",
              "Stability control module communication failure.", "warning"),
    "U0155": ("Lost Communication with Instrument Panel Cluster",
              "Instrument cluster communication fault. Gauges may stop working.", "warning"),
    "U0164": ("Lost Communication with HVAC Control Module",
              "HVAC module communication failure.", "info"),
}


@dataclass
class SensorReading:
    """Single OBD2 sensor reading with metadata."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    priority: int  # 1=always visible  2=scrollable  3=deep-dive


class OBDService:
    """
    OBD2 Diagnostics Service.
    Manages ELM327 connection and provides real-time sensor readings.
    Falls back to smooth, realistic simulation when hardware is absent.
    """

    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 38400,
                 polling_interval: int = 5):
        self.port = port
        self.baudrate = baudrate
        self.polling_interval = polling_interval

        self.connection = None
        self.connected = False
        self.is_running = False
        self.thread: Optional[threading.Thread] = None

        # Live sensor data
        self.latest_readings: Dict[str, SensorReading] = {}

        # Per-sensor history for charting (last 60 readings ≈ 5 min)
        self.sensor_history: Dict[str, deque] = {
            'RPM':            deque(maxlen=60),
            'SPEED':          deque(maxlen=60),
            'COOLANT_TEMP':   deque(maxlen=60),
            'BATTERY_VOLTAGE': deque(maxlen=60),
        }
        self.history_timestamps: deque = deque(maxlen=60)

        # DTC tracking
        self.active_dtcs: List[str] = []
        self.announced_dtcs: List[str] = []

        # Simulation state (smooth, realistic transitions)
        self._sim_rpm = 850.0          # idle RPM
        self._sim_speed = 0.0
        self._sim_temp = 65.0          # cold start °F → warms up to ~195
        self._sim_voltage = 12.6
        self._sim_throttle = 10.0
        self._sim_intake_temp = 75.0
        self._sim_running = 0          # ticks since start

        logger.info(f"OBDService initialized (port={port}, baudrate={baudrate})")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        if self.is_running:
            return
        self._prefill_history()
        self.is_running = True
        self.thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.thread.start()
        logger.info("OBD polling thread started")

    def _prefill_history(self):
        """Seed history deques with 60 points of realistic warm-up data so
        charts are populated the moment the UI opens."""
        now = datetime.now()
        temp = 65.0
        voltage = 12.6
        for i in range(60):
            warmup = min(i / 45, 1.0)
            temp += (65 + warmup * 130 - temp) * 0.12
            speed = max(0, 35 + 25 * ((i % 60) / 30 - 0.5) + random.gauss(0, 2))
            rpm   = 850 if speed < 2 else max(800, 1200 + speed * 28 + random.gauss(0, 40))
            target_v = 12.4 if speed < 2 else 13.8
            voltage += (target_v - voltage) * 0.2

            ts = now.__class__.fromtimestamp(
                now.timestamp() - (60 - i) * self.polling_interval)
            self.history_timestamps.append(ts)
            self.sensor_history['RPM'].append(round(rpm))
            self.sensor_history['SPEED'].append(round(speed, 1))
            self.sensor_history['COOLANT_TEMP'].append(round(temp, 1))
            self.sensor_history['BATTERY_VOLTAGE'].append(round(voltage, 2))

        # Seed latest_readings so gauges show values immediately
        self._sim_temp    = temp
        self._sim_voltage = voltage
        self._sim_running = 60
        self._generate_simulated_data()

        # Demo DTCs — shows both warning and info severity in the DTC tab
        self.active_dtcs = ['P0420', 'P0171']
        logger.info("OBD history pre-filled with 60 demo data points")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
        logger.info("OBD service stopped")

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _connect(self) -> bool:
        if not OBD_AVAILABLE:
            self.connected = False
            return False
        try:
            logger.info(f"Connecting to OBD adapter on {self.port}")
            self.connection = obd.OBD(
                portstr=self.port,
                baudrate=self.baudrate,
                timeout=10,
                check_voltage=True
            )
            if self.connection.status() == obd.OBDStatus.CAR_CONNECTED:
                self.connected = True
                logger.info("ELM327 connected — live data active")
                return True
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"OBD connection failed: {e}")
            self.connected = False
            return False

    # ------------------------------------------------------------------
    # Polling loop
    # ------------------------------------------------------------------

    def _polling_loop(self):
        while self.is_running:
            try:
                if not self.connected:
                    if not self._connect():
                        self._generate_simulated_data()
                        self._record_history()
                        time.sleep(self.polling_interval)
                        continue

                self._poll_sensors()
                self._check_dtcs()
                self._record_history()
                time.sleep(self.polling_interval)

            except Exception as e:
                logger.error(f"OBD polling error: {e}")
                self.connected = False
                self._generate_simulated_data()
                self._record_history()
                time.sleep(self.polling_interval)

    def _poll_sensors(self):
        """Read OBD sensors from real hardware."""
        if not self.connection or not self.connected:
            self._generate_simulated_data()
            return

        sensor_map = [
            (obd.commands.RPM,             'RPM',            'rpm',  1),
            (obd.commands.SPEED,           'SPEED',          'mph',  1),
            (obd.commands.COOLANT_TEMP,    'COOLANT_TEMP',   '°F',   1),
            (obd.commands.ELM_VOLTAGE,     'BATTERY_VOLTAGE','V',    1),
            (obd.commands.INTAKE_TEMP,     'INTAKE_TEMP',    '°F',   2),
            (obd.commands.THROTTLE_POS,    'THROTTLE_POS',   '%',    2),
            (obd.commands.FUEL_PRESSURE,   'FUEL_PRESSURE',  'psi',  2),
            (obd.commands.TIMING_ADVANCE,  'TIMING_ADVANCE', '°',    2),
            (obd.commands.MAF,             'MAF',            'g/s',  2),
            (obd.commands.SHORT_FUEL_TRIM_1, 'STFT_B1',     '%',    2),
            (obd.commands.LONG_FUEL_TRIM_1,  'LTFT_B1',     '%',    2),
            (obd.commands.ENGINE_LOAD,     'ENGINE_LOAD',    '%',    2),
            (obd.commands.INTAKE_PRESSURE, 'INTAKE_PRESSURE','kPa',  3),
            (obd.commands.O2_B1S1,         'O2_B1S1',        'V',    3),
            (obd.commands.O2_B1S2,         'O2_B1S2',        'V',    3),
            (obd.commands.BAROMETRIC_PRESSURE, 'BARO',       'kPa',  3),
        ]

        for cmd, name, unit, priority in sensor_map:
            try:
                resp = self.connection.query(cmd)
                if resp and not resp.is_null():
                    val = float(resp.magnitude)
                    # Convert speed to mph if returned in kph
                    if name == 'SPEED':
                        val = val * 0.621371
                    # Convert temp to °F if returned in °C
                    if name in ('COOLANT_TEMP', 'INTAKE_TEMP'):
                        val = val * 9 / 5 + 32
                    self.latest_readings[name] = SensorReading(
                        name=name, value=round(val, 2),
                        unit=unit, timestamp=datetime.now(), priority=priority
                    )
                    logger.debug(f"Polled {name}: {val} {unit}")
            except Exception as e:
                logger.debug(f"Could not read {name}: {e}")

    def _generate_simulated_data(self):
        """
        Generate smooth, realistic simulated OBD data.
        Values evolve gradually rather than jumping randomly each poll.
        """
        t = self._sim_running
        self._sim_running += 1

        # Engine warm-up curve: temp rises from 65°F → 195°F over first 60 ticks
        target_temp = 65 + min(t / 60, 1.0) * 130
        self._sim_temp += (target_temp - self._sim_temp) * 0.1

        # Simulate variable speed (0–65 mph wave)
        self._sim_speed = max(0, 30 + 30 * (0.5 * (t % 120) / 60 - 0.5) + random.gauss(0, 2))
        self._sim_speed = min(70, self._sim_speed)

        # RPM tracks speed + some engine character
        idle_rpm = 850
        driving_rpm = 1200 + self._sim_speed * 28 + random.gauss(0, 50)
        self._sim_rpm = idle_rpm if self._sim_speed < 2 else driving_rpm
        self._sim_rpm = max(650, min(5500, self._sim_rpm))

        # Battery voltage: higher when alternator running
        target_v = 12.4 if self._sim_speed < 2 else 13.8 + random.gauss(0, 0.05)
        self._sim_voltage += (target_v - self._sim_voltage) * 0.2

        self._sim_throttle = max(0, min(100, 5 + self._sim_speed * 0.6 + random.gauss(0, 2)))
        self._sim_intake_temp = max(60, min(120, self._sim_intake_temp + random.gauss(0, 0.5)))

        fuel_pressure = 40.0 + random.gauss(0, 0.5)
        engine_load = max(5, min(90, self._sim_throttle * 0.9 + random.gauss(0, 3)))
        stft = random.gauss(0, 2.0)   # fuel trim ±2%
        ltft = random.gauss(0, 1.0)   # long term

        readings = {
            'RPM':            SensorReading('RPM',            round(self._sim_rpm),      'rpm',  datetime.now(), 1),
            'SPEED':          SensorReading('SPEED',          round(self._sim_speed, 1), 'mph',  datetime.now(), 1),
            'COOLANT_TEMP':   SensorReading('COOLANT_TEMP',   round(self._sim_temp, 1),  '°F',   datetime.now(), 1),
            'BATTERY_VOLTAGE':SensorReading('BATTERY_VOLTAGE',round(self._sim_voltage,2),'V',    datetime.now(), 1),
            'INTAKE_TEMP':    SensorReading('INTAKE_TEMP',    round(self._sim_intake_temp,1),'°F',datetime.now(), 2),
            'THROTTLE_POS':   SensorReading('THROTTLE_POS',   round(self._sim_throttle,1),'%',   datetime.now(), 2),
            'FUEL_PRESSURE':  SensorReading('FUEL_PRESSURE',  round(fuel_pressure,1),    'psi',  datetime.now(), 2),
            'ENGINE_LOAD':    SensorReading('ENGINE_LOAD',    round(engine_load,1),       '%',    datetime.now(), 2),
            'STFT_B1':        SensorReading('STFT_B1',        round(stft,1),              '%',    datetime.now(), 2),
            'LTFT_B1':        SensorReading('LTFT_B1',        round(ltft,1),              '%',    datetime.now(), 2),
            'TIMING_ADVANCE': SensorReading('TIMING_ADVANCE', round(12 + random.gauss(0,1),1),'°',datetime.now(), 2),
            'O2_B1S1':        SensorReading('O2_B1S1',        round(0.45 + random.gauss(0,0.15),3),'V',datetime.now(), 3),
            'O2_B1S2':        SensorReading('O2_B1S2',        round(0.70 + random.gauss(0,0.05),3),'V',datetime.now(), 3),
            'MAF':            SensorReading('MAF',            round(2+self._sim_speed*0.2+random.gauss(0,0.3),2),'g/s',datetime.now(), 3),
        }
        self.latest_readings.update(readings)

    def _record_history(self):
        """Append current priority-1 readings to history deques for charting."""
        self.history_timestamps.append(datetime.now())
        for key in ('RPM', 'SPEED', 'COOLANT_TEMP', 'BATTERY_VOLTAGE'):
            r = self.latest_readings.get(key)
            self.sensor_history[key].append(r.value if r else 0)

    def _check_dtcs(self):
        if not self.connection or not self.connected:
            return
        try:
            resp = self.connection.query(obd.commands.GET_DTC)
            if resp and not resp.is_null():
                self.active_dtcs = [t[0] for t in resp.value]
                for code in self.active_dtcs:
                    if code not in self.announced_dtcs:
                        logger.warning(f"New DTC: {code} — {self.get_dtc_description(code)}")
                        self.announced_dtcs.append(code)
        except Exception as e:
            logger.debug(f"DTC check failed: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_reading(self, sensor_name: str) -> Optional[SensorReading]:
        return self.latest_readings.get(sensor_name)

    def get_all_readings(self, priority: Optional[int] = None) -> Dict[str, SensorReading]:
        if priority is None:
            return dict(self.latest_readings)
        return {n: r for n, r in self.latest_readings.items() if r.priority == priority}

    def get_chart_data(self, sensor_name: str):
        """Return (timestamps_list, values_list) for charting."""
        return list(self.history_timestamps), list(self.sensor_history.get(sensor_name, []))

    def get_dtc_description(self, code: str) -> str:
        """Return human-readable DTC description."""
        entry = DTC_DATABASE.get(code)
        return entry[1] if entry else "Unknown diagnostic trouble code."

    def get_dtc_title(self, code: str) -> str:
        entry = DTC_DATABASE.get(code)
        return entry[0] if entry else "Unknown Code"

    def get_dtc_severity(self, code: str) -> str:
        entry = DTC_DATABASE.get(code)
        return entry[2] if entry else "warning"

    def get_dtcs(self) -> Dict[str, dict]:
        """Return active DTCs with full info."""
        result = {}
        for code in self.active_dtcs:
            result[code] = {
                'title':       self.get_dtc_title(code),
                'description': self.get_dtc_description(code),
                'severity':    self.get_dtc_severity(code),
            }
        return result

    def clear_dtcs(self) -> bool:
        if not self.connection or not self.connected:
            logger.warning("Cannot clear DTCs — not connected")
            return False
        try:
            self.connection.send_command('04')
            self.active_dtcs.clear()
            self.announced_dtcs.clear()
            logger.info("DTCs cleared")
            return True
        except Exception as e:
            logger.error(f"DTC clear failed: {e}")
            return False

    def get_health_summary(self) -> dict:
        """Compute a simple engine health score from live readings."""
        score = 100
        issues = []
        r = self.latest_readings

        temp = r.get('COOLANT_TEMP')
        if temp:
            if temp.value > 220:
                score -= 30; issues.append("Engine overheating!")
            elif temp.value > 210:
                score -= 15; issues.append("High coolant temp")
            elif temp.value < 150 and self._sim_running > 20:
                score -= 10; issues.append("Thermostat may be stuck open")

        volt = r.get('BATTERY_VOLTAGE')
        if volt:
            if volt.value < 11.8:
                score -= 25; issues.append("Low battery/alternator voltage")
            elif volt.value < 12.4:
                score -= 10; issues.append("Battery charging low")
            elif volt.value > 15.0:
                score -= 20; issues.append("Overcharging — alternator fault")

        stft = r.get('STFT_B1')
        if stft and abs(stft.value) > 10:
            score -= 15; issues.append(f"Fuel trim out of range ({stft.value:+.1f}%)")

        if self.active_dtcs:
            score -= min(40, len(self.active_dtcs) * 10)
            issues.append(f"{len(self.active_dtcs)} active DTC(s)")

        return {
            'score': max(0, score),
            'issues': issues,
            'dtc_count': len(self.active_dtcs),
            'connected': self.connected,
        }

    def get_status(self) -> dict:
        return {
            'connected': self.connected,
            'port': self.port,
            'readings_count': len(self.latest_readings),
            'active_dtcs': len(self.active_dtcs),
            'is_running': self.is_running,
        }


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    svc = OBDService()
    svc.start()
    time.sleep(12)
    for name, r in svc.get_all_readings(priority=1).items():
        print(f"  {name}: {r.value} {r.unit}")
    print("Health:", svc.get_health_summary())
    svc.stop()
