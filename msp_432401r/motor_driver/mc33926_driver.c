/*
 * mc33926_driver.c
 *
 *  Created on: 17 nov 2025
 *      Author: daniele
 */
#include "mc33926_driver.h"


/*Funzioni private*/
static void initGPIO(void);
static void initPWM(void);
static void initADC(void);
static uint16_t readADC(uint8_t memIndex);

void MC33926_Init(void){
    initGPIO();
    initPWM();
    initADC();
}

static void initGPIO(void){
    M1_DIR_PORT->DIR |= M1_DIR_PIN; //configura direzione Motor 1 come output
    M1_DIR_PORT->OUT &= ~M1_DIR_PIN; //metto motore in modalità "avanti"

    M2_DIR_PORT->DIR |= M2_DIR_PIN;
    M2_DIR_PORT->OUT &= ~M2_DIR_PIN;    // Default: forward (LOW)

    M3_DIRA_PORT->DIR |= M3_DIRA_PIN;
    M3_DIRB_PORT->DIR |= M3_DIRA_PIN;

    M3_DIRA_PORT->OUT |= M3_DIRA_PIN;
    M3_DIRB_PORT->OUT &= ~M3_DIRB_PIN;

    ND2_PORT->DIR |= ND2_PIN; //configura Enable pin come output
    ND2_PORT->OUT |= ND2_PIN; //driver acceso di default (HIGH)

    NSF_PORT->DIR &= ~NSF_PIN; //configura Fault pin come input

    /*configuro PWM pins con la funzione primaria Timer_A0.1/2*/
    M1_PWM_PORT->SEL0 |= M1_PWM_PIN;
    M1_PWM_PORT->SEL1 &= ~M1_PWM_PIN;
    M1_PWM_PORT->DIR |= M1_PWM_PIN; //Output direction
    M2_PWM_PORT->SEL0 |= M2_PWM_PIN;
    M2_PWM_PORT->SEL1 &= ~M2_PWM_PIN;
    M2_PWM_PORT->DIR |= M2_PWM_PIN;
    M3_PWM_PORT->SEL0 |= M3_PWM_PIN;
    M3_PWM_PORT->SEL1 &= ~M3_PWM_PIN;
    M3_PWM_PORT->DIR |= M3_PWM_PIN;

    /* Motor 4 (pompa) - GPIO puri, no funzione timer */
    M4_DIRA_PORT->SEL0 &= ~M4_DIRA_PIN;
    M4_DIRA_PORT->SEL1 &= ~M4_DIRA_PIN;
    M4_DIRA_PORT->DIR  |= M4_DIRA_PIN;
    M4_DIRA_PORT->OUT  &= ~M4_DIRA_PIN;

    M4_DIRB_PORT->SEL0 &= ~M4_DIRB_PIN;
    M4_DIRB_PORT->SEL1 &= ~M4_DIRB_PIN;
    M4_DIRB_PORT->DIR  |= M4_DIRB_PIN;
    M4_DIRB_PORT->OUT  &= ~M4_DIRB_PIN;

    M4_PWM_PORT->SEL0 &= ~M4_PWM_PIN;
    M4_PWM_PORT->SEL1 &= ~M4_PWM_PIN;
    M4_PWM_PORT->DIR  |= M4_PWM_PIN;
    M4_PWM_PORT->OUT  &= ~M4_PWM_PIN;
}

static void initPWM(void){
    TIMER_A0->CTL = 0; //Stoppo timer prima di configurarlo
    /* Configura il control register del timer: */
    TIMER_A0->CTL = TIMER_A_CTL_SSEL__SMCLK | TIMER_A_CTL_MC__UP | TIMER_A_CTL_CLR;
    /*setto registro di comparazione a cui il timer si resetta*/
    TIMER_A0->CCR[0] = PWM_PERIOD;
    //in modalità outmod7, all'inizio del periodo il pin è HIGH
    //poi quando il timer arriva al valore in CCR1 il pin scende a LOW
    //per poi ritornare HIGH quando raggiunge CCR0
    TIMER_A0->CCTL[1] = OUTMOD_7;
    TIMER_A0->CCR[1] = 0; //duty cycle iniziale al 0 %
    /* Configure CCR2 for Motor 2 PWM (P2.5 = TA0.2) */
    TIMER_A0->CCTL[2] = OUTMOD_7;
    TIMER_A0->CCR[2] = 0;
    /* COnfigura CCR3 per motore 3 */
    TIMER_A0->CCTL[4] = OUTMOD_7;
    TIMER_A0->CCR[4] = 0;
}

static void initADC(void){
    //cofiguro gli ADC pins come input analogici(funzione terziaria)
    P4->SEL0 |= (BIT0 | BIT2 | BIT4);
    P4->SEL1 |= (BIT0 | BIT2 | BIT4);
    //adc14 -> modulo hardware adc a 14 bit di risoluzione
    ADC14->CTL0 = ADC14_CTL0_SHT0_2 |  //Sample-and-hold time = 16 cicli di clock
                  ADC14_CTL0_SHP |     //Sample-and-hold Pulse = usa timer interno per decidere quanto campionare
                  ADC14_CTL0_ON;       //Acceende l'ADC14

    //L'ADC converte tensioni (0-3.3V) in numeri digitali di 14 bit (16384 valori possibili)
        //0V -> 0 ; 1.65V -> 8192 ; 3.3V -> 16383
    ADC14->CTL1 = ADC14_CTL1_RES_3;
    /* Configure Memory Control for Motor 1 (MEM13, channel A13) */
    ADC14->MCTL[M1_FB_MEM] = ADC14_MCTLN_INCH_13;
    /* Configure Memory Control for Motor 2 (MEM11, channel A11) */
    ADC14->MCTL[M2_FB_MEM] = ADC14_MCTLN_INCH_11;
    /* Configure Memory Control for Motor 3 (MEM9, channel A9) */
    ADC14->MCTL[M3_FB_MEM] = ADC14_MCTLN_INCH_9;
}

void MC33926_SetMotor1Speed(int16_t speed){
    uint8_t reverse = 0;
    if(speed<0){
        speed = -speed;
        reverse = 1;
    }
    if(speed > MAX_SPEED){
        speed = MAX_SPEED; //tronca
    }
    if (reverse){
        M1_DIR_PORT->OUT |= M1_DIR_PIN; //HIGH = backward
    }else{
        M1_DIR_PORT->OUT &= ~M1_DIR_PIN; //LOW = forward
    }
    //uso uint32_t perchè facendo *2400 rischio di andare in overflow
    uint16_t dutyCycle = ((uint32_t)speed * PWM_PERIOD)/MAX_SPEED;
    TIMER_A0->CCR[1] = dutyCycle;
}

void MC33926_SetMotor2Speed(int16_t speed){
    uint8_t reverse = 0;
    if(speed<0){
        speed = -speed;
        reverse = 1;
    }
    if(speed > MAX_SPEED){
        speed = MAX_SPEED; //tronca
    }
    if (reverse){
        M2_DIR_PORT->OUT |= M2_DIR_PIN; //HIGH = backward
    }else{
        M2_DIR_PORT->OUT &= ~M2_DIR_PIN; //LOW = forward
    }
    //uso uint32_t perchè facendo *2400 rischio di andare in overflow
    uint16_t dutyCycle = ((uint32_t)speed * PWM_PERIOD)/MAX_SPEED;
    TIMER_A0->CCR[2] = dutyCycle;
}

void MC33926_SetMotor3Speed(int16_t speed){
    uint8_t reverse = 0;
    if(speed<0){
        speed = -speed;
        reverse = 1;
    }
    if(speed > MAX_SPEED){
        speed = MAX_SPEED; //tronca
    }
    if (reverse){
        M3_DIRA_PORT->OUT &= ~M3_DIRA_PIN; //0
        M3_DIRB_PORT->OUT |= M3_DIRB_PIN;  //1
    }else{ //speed >= 0
        if(speed==0){
            M3_DIRA_PORT->OUT &= ~M3_DIRA_PIN;  //0
            M3_DIRB_PORT->OUT &= ~M3_DIRB_PIN;  //0
        }else{
            M3_DIRA_PORT->OUT |= M3_DIRA_PIN;
            M3_DIRB_PORT->OUT &= ~M3_DIRB_PIN;
        }
    }
    //uso uint32_t perchè facendo *2400 rischio di andare in overflow
    uint16_t dutyCycle = ((uint32_t)speed * PWM_PERIOD)/MAX_SPEED;
    TIMER_A0->CCR[4] = dutyCycle;
}

void MC33926_SetMotor4Speed(int16_t speed){
    if(speed > 0){
        M4_DIRA_PORT->OUT |= M4_DIRA_PIN;    // dirA = 1
        M4_DIRB_PORT->OUT &= ~M4_DIRB_PIN;   // dirB = 0
        M4_PWM_PORT->OUT  |= M4_PWM_PIN;     // enable = HIGH
    }else if(speed < 0){
        M4_DIRA_PORT->OUT &= ~M4_DIRA_PIN;   // dirA = 0
        M4_DIRB_PORT->OUT |= M4_DIRB_PIN;    // dirB = 1
        M4_PWM_PORT->OUT  |= M4_PWM_PIN;     // enable = HIGH
    }else{
        M4_DIRA_PORT->OUT &= ~M4_DIRA_PIN;   // dirA = 0
        M4_DIRB_PORT->OUT &= ~M4_DIRB_PIN;   // dirB = 0
        M4_PWM_PORT->OUT  &= ~M4_PWM_PIN;    // enable = LOW
    }
}

void MC33926_SetSpeeds(int16_t m1Speed, int16_t m2Speed, int16_t m3Speed, int16_t m4Speed){
    MC33926_SetMotor1Speed(m1Speed);
    MC33926_SetMotor2Speed(m2Speed);
    MC33926_SetMotor3Speed(m3Speed);
    MC33926_SetMotor4Speed(m4Speed);
}

static uint16_t readADC(uint8_t memIndex){ //memIndex = 13 o 11 per leggere Motor 1 o Motor 2
    /* ADC14_CTL0_ENC: abilita l'ADC a fare conversioni
     *  ADC14_CTL0_SC : fa partire la conversione adesso
     */
    ADC14->CTL0 |= ADC14_CTL0_ENC | ADC14_CTL0_SC;
    //meglio usare interrupt?
    while (ADC14->CTL0 & ADC14_CTL0_BUSY); //ADC14_CTL0_BUSY = bit che indica "conversione in corso"

    /* Disable conversion */
    ADC14->CTL0 &= ~ADC14_CTL0_ENC;
    /* Return result from memory */
    return ADC14->MEM[memIndex];
}

uint16_t MC33926_GetMotor1Current(void){
    uint16_t adcValue = readADC(M1_FB_MEM);
    /* Current calculation:
         * MC33926 current sense: 525mV per Ampere
         * MSP432 ADC: 14-bit (0-16383), 3.3V reference
         *
         * Voltage (V) = adcValue * 3.3 / 16384
         * Current (A) = Voltage / 0.525
         * Current (mA) = adcValue * 3.3 * 1000 / (0.525 * 16384)
         *              = adcValue * 3300 / 8601.6
         *              = adcValue * 0.3837
         *              ≈ adcValue * 6287 / 16384
         */
        uint32_t currentMilliamps = ((uint32_t)adcValue * 6287) / 16384;
        return (uint16_t)currentMilliamps;
}
uint16_t MC33926_GetMotor2Current(void)
{
    uint16_t adcValue = readADC(M2_FB_MEM);  // Legge MEM[11]
    uint32_t currentMilliamps = ((uint32_t)adcValue * 6287) / 16384;
    return (uint16_t)currentMilliamps;
}

uint16_t MC33926_GetMotor3Current(void)
{
    uint16_t adcValue = readADC(M3_FB_MEM);
    uint32_t currentMilliamps = ((uint32_t)adcValue * 6287) / 16384;
    return (uint16_t)currentMilliamps;
}

uint8_t MC33926_GetFault(void)
{
    /* nSF pin is active LOW (LOW = fault present) */
    return (NSF_PORT->IN & NSF_PIN) ? 0 : 1;
}
void MC33926_Enable(void)
{
    /* nD2 is active HIGH (HIGH = enabled) */
    ND2_PORT->OUT |= ND2_PIN;
}

void MC33926_Disable(void)
{
    /* nD2 is active HIGH (LOW = disabled, coast mode) */
    ND2_PORT->OUT &= ~ND2_PIN;
}



