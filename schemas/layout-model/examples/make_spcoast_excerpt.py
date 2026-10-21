"""Writes spcoast-excerpt.json, the ADR 0008 §6 example, in canonical form. Run: uv run python schemas/layout-model/examples/make_spcoast_excerpt.py"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools import layout_model  # noqa: E402

model = {
    "schema": "layout-model/v2.0.0",
    "layout": {
        "name": "SPCoast", "railroad": "SPCoast", "division": "South",
        "settings": {"era": "1970s", "rulebook": "SP 1969"},
        "transports": {
            "CMRInet": {"kind": "CMRI", "params": {"port": "/dev/cu.usbserial-CMRI", "baud": "28800"}, "host": "CMRI Host"},
            "MQTT": {"kind": "MQTT", "params": {"broker": "192.168.1.21:1883", "topic": "ctc/SPCoast/codeline/"}},
        },
        "codelines": {"AAR Tokens@MQTT": {"encoding": "AAR", "transport": "MQTT"}},
        "processors": {
            "Sargent": {"side": "field", "board": "cpNode Xiao", "chips": {"0x20": {"ic": "MCP23017"}, "0x40/pwm": {"ic": "PCA9685"}, "0x40/servo": {"ic": "PCA9685"}}},
            "Luchessa": {"side": "field", "board": "cpNode Xiao", "chips": {"0x20": {"ic": "MCP23017"}, "0x21": {"ic": "MCP23017"}}},
            "Corporal": {"side": "field", "board": "cpNode Xiao", "chips": {"0x20": {"ic": "MCP23017"}}},
            "Caltrain": {"side": "field", "board": "cpNode", "transport": "CMRInet", "address": "30", "chips": {"CMRI": {"ic": "CMRI"}}},
            "SPCoast South": {"side": "office", "board": "ESP32", "chips": {"0x2C": {"ic": "MAX7313"}}},
            "Plant Host": {"side": "field", "board": "macOS app",
                           "description": "Day 0: hosts the field units that have no field processor yet; their devices are absent and the emulator mocks them"},
            "CMRI Host": {"side": "field", "board": "macOS app",
                          "description": "FieldUnit + CMRInet host: runs the logic of the all-CMRI field units and polls the line"},
            "JMRI Host": {"side": "field", "board": "macOS app",
                          "description": "FieldUnit + MQTT client: runs the logic of the all-JMRI field units"},
            "JMRI": {"side": "field", "board": "JMRI", "transport": "MQTT", "chips": {"MQTT": {"ic": "JMRI"}},
                     "description": "Remote I/O node: JMRI drives the devices over MQTT; a pin is the JMRI object a driver stands for (simpleton)"},
        },
    },
    "interlockings": {
        "Sargent": {
            "controlPoints": {"Sargent": {"milepost": 83.5}},
            "appliances": {
                "835": {"appliance": "switch", "style": "lock", "controlPoint": "Sargent:Sargent", "osCircuit": "Sargent:835T1"},
                "836NAB": {"appliance": "mast", "style": "double", "heads": {"A": {"style": "CPL"}, "B": {"style": "CPL"}}},
            },
            "codelines": [{"codeline": "AAR Tokens@MQTT", "address": "Sargent"}],
            "fieldUnit": {"host": "Sargent"},
            "devices": [
                {"type": {"appliance": "switch", "style": ["powered", "lock", "dual"]}, "serves": "Sargent:835",
                 "bindings": [{"function": "M", "chip": "Sargent/0x20", "pin": "B1"}, {"function": "N", "chip": "Sargent/0x20", "pin": "B2"}]},
                {"type": {"appliance": "head"}, "serves": "Sargent:836NAB", "address": "1",
                 "bindings": [{"function": "LAMP", "chip": "Sargent/0x40/pwm", "pin": "B1"}]},
            ],
        },
        "Luchessa": {
            "controlPoints": {"CP Luchessa": {}, "CP Gilroy": {}, "CP Carnadero": {}},
            "codelines": [{"codeline": "AAR Tokens@MQTT", "address": "Luchessa"}],
            "fieldUnit": {"host": "Luchessa"},
        },
        "Corporal": {
            "codelines": [{"codeline": "AAR Tokens@MQTT", "address": "Corporal"}],
            "fieldUnit": {"host": "Corporal"},
        },
        "Gilroy Caltrain": {
            "controlPoints": {"Gilroy Caltrain": {}},
            "appliances": {
                "773": {"appliance": "switch", "style": "powered", "controlPoint": "Gilroy Caltrain:Gilroy Caltrain"},
                "774NAB": {"appliance": "mast", "style": "double", "heads": {"A": {"style": "CPL"}, "B": {"style": "CPL"}}},
            },
            "codelines": [{"codeline": "AAR Tokens@MQTT", "address": "Gilroy Caltrain"}],
            "fieldUnit": {"host": "CMRI Host"},
            "devices": [
                {"type": {"appliance": "head"}, "serves": "Gilroy Caltrain:774NAB",
                 "bindings": [{"function": "LAMP", "chip": "Caltrain/CMRI", "pin": "OUT.7"}]},
                {"type": {"appliance": "switch", "style": "powered"}, "serves": "Gilroy Caltrain:773",
                 "bindings": [{"function": "N", "chip": "Caltrain/CMRI", "pin": "OUT.1"}, {"function": "NWK", "chip": "Caltrain/CMRI", "pin": "IN.1"}]},
            ],
        },
        "Gilroy Interchange": {
            "controlPoints": {"Gilroy North": {"milepost": 77.7}, "Gilroy South": {"milepost": 78.1}},
            "appliances": {
                "777": {"appliance": "switch", "style": "lock", "controlPoint": "Gilroy Interchange:Gilroy North", "osCircuit": "Gilroy Interchange:777T1"},
                "781": {"appliance": "switch", "style": "lock", "controlPoint": "Gilroy Interchange:Gilroy South", "osCircuit": "Gilroy Interchange:781T1"},
            },
            "codelines": [{"codeline": "AAR Tokens@MQTT", "address": "Gilroy Interchange"}],
            "fieldUnit": {"host": "JMRI Host"},
            "devices": [
                {"type": {"appliance": "switch", "style": ["powered", "lock", "dual"]}, "serves": "Gilroy Interchange:777",
                 "bindings": [{"function": "M", "chip": "JMRI/MQTT", "pin": "Turnout"},
                              {"function": "N", "chip": "JMRI/MQTT", "pin": "Turnout-Feedback.N"},
                              {"function": "R", "chip": "JMRI/MQTT", "pin": "Turnout-Feedback.R"}]},
            ],
        },
        "Watsonville": {
            "description": "Day 0: no field processor yet; its devices are absent and the emulator mocks them",
            "codelines": [{"codeline": "AAR Tokens@MQTT", "address": "Watsonville"}],
            "fieldUnit": {"host": "Plant Host"},
        },
    },
    "machines": {
        "SPCoast South": {
            "panelStyle": "US&S 506 lever panel",
            "columns": {"13": {"interlocking": "Sargent"}},
            "attachments": [{"interlocking": "Sargent", "columns": ["13"], "codeline": "AAR Tokens@MQTT"}],
            "officeUnit": {"host": "SPCoast South"},
            "devices": [
                {"type": {"appliance": "lever", "style": "lock"}, "serves": "Sargent:835", "column": "SPCoast South:13",
                 "bindings": [{"function": "WLS", "chip": "SPCoast South/0x2C", "pin": "A7"}]},
            ],
        }
    },
    "provenance": {
        "sourceType": "KiCad",
        "compiler": {"name": "kicad2layout", "version": "0.0.0-example"},
        "source": {"path": "SPCoast/SPCoast.kicad_pro", "sha256": hashlib.sha256(b"example").hexdigest(), "describe": "example"},
        "libraries": {"Railroad-Trackplan": "example", "Railroad-Field": "example", "Railroad-HardwareIO": "example", "Railroad-Office": "example"},
        "referenceData": {"chips": "example", "boards": "example", "encodings": "example"},
    },
}

if __name__ == "__main__":
    layout_model.validate(model)
    layout_model.write(Path(__file__).with_name("spcoast-excerpt.json"), model)
    print("ok")
