# Versy

Robot autonomo su Raspberry Pi con visione artificiale e state machine.

## Setup

```bash
# Crea virtual environment
python3 -m venv .venv

# Attiva virtual environment
source .venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt
```

## Avvio

```bash
cd raspberry-pi
python main.py
```

Stop con `Ctrl+C`.

## Struttura

```
raspberry-pi/
├── main.py            # Entry point
├── state_machine.py   # State machine principale
├── robot/             # Hardware (motori, sensori)
├── vision/            # Computer vision (ArUco)
├── machine/           # Logica stati
├── config/            # Configurazione
├── utils/             # Utility (logging, debug)
└── software_testing/  # Test
```
