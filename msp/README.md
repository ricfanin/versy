# Versy4 - Driver motori MSP432P401R

Firmware per MSP432P401R che controlla 4 motori tramite driver MC33926, comandati via I2C da un Raspberry Pi.

## Architettura

Il Raspberry Pi invia comandi I2C (indirizzo `0x10`) con 2 byte:
1. **Numero motore** (0-3)
2. **Velocita** (int8: -128 a +127, il segno determina la direzione)

Per i motori 1-3 il valore viene moltiplicato x4 (range finale -400/+400).
Il motore 4 (pompa) usa il valore diretto: qualsiasi valore != 0 accende, il segno imposta la direzione.

## Pinout

### Motor 1
| Funzione | Pin | Note |
|----------|-----|------|
| DIR      | P6.6 | LOW = avanti, HIGH = indietro |
| PWM      | P2.4 | Timer_A0.1 |
| FB (ADC) | A13 (P4.0) | Lettura corrente |

### Motor 2
| Funzione | Pin | Note |
|----------|-----|------|
| DIR      | P2.6 | LOW = avanti, HIGH = indietro |
| PWM      | P2.5 | Timer_A0.2 |
| FB (ADC) | A11 (P4.2) | Lettura corrente |

### Motor 3
| Funzione | Pin | Note |
|----------|-----|------|
| DIRA     | P6.7 | Forward: 1 |
| DIRB     | P5.7 | Forward: 0 |
| PWM      | P2.7 | Timer_A0.4 |
| FB (ADC) | A9 (P4.4) | Lettura corrente |

### Motor 4 (pompa - ON/OFF, no PWM)
| Funzione | Pin | Note |
|----------|-----|------|
| DIRA     | P3.5 | Forward: 1 (originariamente P5.0, non funzionante in HW) |
| DIRB     | P5.1 | Forward: 0 |
| Enable   | P5.2 | GPIO, HIGH = accesa |

### Controllo generale
| Funzione | Pin | Note |
|----------|-----|------|
| ND2 (Enable driver) | P3.0 | HIGH = driver acceso |
| NSF (Fault) | P3.2 | LOW = errore |

### Comunicazione
| Funzione | Pin |
|----------|-----|
| I2C SDA  | P1.6 |
| I2C SCL  | P1.7 |
| UART TX  | P1.3 |
| UART RX  | P1.2 |

## Configurazione

- Clock: DCO a 48 MHz (MCLK e SMCLK)
- PWM: 20 KHz (periodo 2400, Timer_A0 in modalita UP)
- UART: 115200 baud (debug)
- I2C: slave, indirizzo 0x10
- ADC: 14 bit, lettura corrente motori

## API driver (mc33926_driver.h)

```c
void MC33926_Init(void);                  // Init GPIO, PWM, ADC
void MC33926_Enable(void);                // Accende il driver
void MC33926_Disable(void);               // Spegne il driver (coast mode)

void MC33926_SetMotor1Speed(int16_t speed); // -400..+400
void MC33926_SetMotor2Speed(int16_t speed);
void MC33926_SetMotor3Speed(int16_t speed);
void MC33926_SetMotor4Speed(int16_t speed); // Pompa: >0 forward, <0 reverse, 0 spenta
void MC33926_SetSpeeds(int16_t m1, int16_t m2, int16_t m3, int16_t m4);

uint16_t MC33926_GetMotor1Current(void);  // Ritorna mA
uint16_t MC33926_GetMotor2Current(void);
uint16_t MC33926_GetMotor3Current(void);
uint8_t  MC33926_GetFault(void);          // 1 = errore, 0 = OK
```

## Protocollo I2C

Il Raspberry Pi (master) invia 2 byte per transazione:

| Byte | Contenuto | Valori |
|------|-----------|--------|
| 1    | Numero motore | 0=M1, 1=M2, 2=M3, 3=Pompa |
| 2    | Velocita (int8) | -128..+127 |

Il debug viene stampato via UART nel formato `M<n>:<+/-valore>`.
