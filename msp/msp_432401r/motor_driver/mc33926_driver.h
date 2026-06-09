/*
 * mc33926_driver.h
 *
 *  Created on: 17 nov 2025
 *      Author: daniele
 */

#ifndef MC33926_DRIVER_H
#define MC33926_DRIVER_H
#include <stdint.h>
#include "msp432.h"

/* configurazione dei pin (default per la MSP432P401R LaunchPad) */

/* Motor 1 pins --------------------------------------*/
#define M1_DIR_PORT P6  //Porta di direzione
#define M1_DIR_PIN BIT6 //pin P2.7: LOW = motore và avanti ; HIGH= motore và indietro
#define M1_PWM_PORT P2  //porta del PWM di Motor 1
#define M1_PWM_PIN BIT4 //Il pin P2.4 genera il segnale PWM, Timer_A0.1
#define M1_FB_ADC_CH 13 //canale ADC numero 13 legge corrente di Motor 1
#define M1_FB_MEM 13  //risultato della lettura ADC verrà salvato in MEM[13] dell'ADC 13

/* Motor 2 pins -----------------------------*/
#define M2_DIR_PORT P2  //Porta di direzione
#define M2_DIR_PIN BIT6 //pin P2.6: LOW = motore và avanti ; HIGH= motore và indietro
#define M2_PWM_PORT P2  //porta del PWM di Motor 1
#define M2_PWM_PIN BIT5 //Il pin P2.5 genera il segnale PWM, Timer_A0.2
#define M2_FB_ADC_CH 11 //canale ADC numero 11 legge corrente di Motor 2
#define M2_FB_MEM 11  //risultato della lettura ADC verrà salvato in MEM[11] dell'ADC 11

/*Motor 3 pins -----------------------------------*/
#define M3_DIRA_PORT P6
#define M3_DIRA_PIN BIT7   //avanti :1
#define M3_DIRB_PORT P5
#define M3_DIRB_PIN BIT7   //avanti : 0
#define M3_PWM_PORT P2
#define M3_PWM_PIN BIT7  //pin P2.7 controllato da Timer_A0.4
#define M3_FB_ADC_CH 9
#define M3_FB_MEM 9


/* Motor 4 pins (pompa - no PWM, solo ON/OFF) */
#define M4_DIRA_PORT P3
#define M4_DIRA_PIN  BIT5   // P3.5 (P5.0 non funziona in hardware)
#define M4_DIRB_PORT P5
#define M4_DIRB_PIN  BIT1   // P5.1
#define M4_PWM_PORT  P5
#define M4_PWM_PIN   BIT2   // P5.2 (GPIO, non timer)

/*Pin di controllo generale--------------------*/
#define ND2_PORT P3
#define ND2_PIN BIT0 //P3.0 a HIGH -> driver acceso ; P3.0 a LOW-> driver spento
#define NSF_PORT P3 // P3.2 è segnale d'allarme del driver
#define NSF_PIN BIT2 // P3.2 a HIGH -> tutto OK ; P3.2 a LOW -> c'è un problema

/*PWM configuration --------------------------*/
#define PWM_PERIOD 2400 //Clock/period = 48 Mhz/2400 = 20KHz
#define MAX_SPEED 400   //Velocità massima è 400 (100% PWM)

/* Funzione di setup iniziale, da chiamare una volta sola all'inizio del programma
 *  -configura i pin GPIO
 *  -Imposta il Timer per generare PWM
 *  -Prepara ADC per leggere corrente dei motori
 */
void MC33926_Init(void);

/*Controlla Motor 1
 * Parametro speed(un numero da -400 a 400):
 *     -Positivo: motore gira in avanti
 *     -Negativo: motore gira indietro
 *     -Zero: motore fermo
 * Conerte la velocità in duty cycle del PWM
 */
void MC33926_SetMotor1Speed(int16_t speed);


/*Controlla Motor 2
 * Parametro speed(un numero da -400 a 400):
 *     -Positivo: motore gira in avanti
 *     -Negativo: motore gira indietro
 *     -Zero: motore fermo
 * Conerte la velocità in duty cycle del PWM
 */
void MC33926_SetMotor2Speed(int16_t speed);

void MC33926_SetMotor3Speed(int16_t speed);

/*Controlla Motor 4 (pompa - ON/OFF, no PWM)
 * Parametro speed:
 *     -Positivo: pompa accesa (avanti)
 *     -Negativo: pompa accesa (reverse)
 *     -Zero: pompa spenta
 */
void MC33926_SetMotor4Speed(int16_t speed);

/*Controlla tutti i contemporaneamente
 *
 */
void MC33926_SetSpeeds(int16_t m1Speed, int16_t m2Speed, int16_t m3Speed, int16_t m4Speed);


/*Misura quanta corrente sta consumando Motor1, per rilevare se è sotto sforzo
 * Ritorna: numero in milliampere(mA)
 */
uint16_t MC33926_GetMotor1Current(void);
/*Misura quanta corrente sta consumando Motor2, per rilevare se è sotto sforzo
 * Ritorna: numero in milliampere(mA)
 */
uint16_t MC33926_GetMotor2Current(void);

uint16_t MC33926_GetMotor3Current(void);


/*Controlla se c'è un problema hardware grave (SovraCorrente, SUrriscaldamento o Sottotensione)
 * -Ritorna:
 *      -1 -> c'è un problema
 *      -0 -> Tutto OK
 */
uint8_t MC33926_GetFault(void);


/* Aceende il driver motori. Da usare subito dopo MC33926_Init()
 *
 */
void MC33926_Enable(void);

/* Spegne driver dei motori - i motori girano liberamente (coast mode)
 * Da usare per:
 *      -Emergenza
 *      -Risparmio energetico
 *      -Manutenzione
 */


void MC33926_Disable(void);
#endif /* MOTOR_DRIVER_MC33926_DRIVER_H_ */
