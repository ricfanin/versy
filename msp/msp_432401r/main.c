#include "msp.h"

#include <stdio.h>
#include <stdint.h>
#include "motor_driver/mc33926_driver.h"

/*Configurazione I2C*/
#define I2C_SLAVE_ADDRESS 0x10

/*variabili globali per comunicazione I2C
 * -Uso volatile per variabili che possono erre modificate da ISR
 * */
volatile uint8_t n_motore = 0;   //Numero motore: 0 o 1
volatile int16_t value = 0;  //Speed value: da -128 a +127(sarà moltiplicato per 4)
volatile uint8_t byte_count = 0;   //Counter di byte per transazione I2C

/* Global variables for deferred UART debug printing
 * Perchè stampare via UART nell'interrupt è lento, quindi imposto flag e stampa nel main
 * */
volatile uint8_t debug_ready = 0;  //Flag: new debug message ready to print
volatile uint8_t debug_motor = 0;  //Motor number for debug message (0:M!, 1: M2 , 2: M3)
volatile int16_t debug_value = 0;  //Valore per il messaggio di debug

/* Function prototypes */
static void initSystemClock(void);
static void initUART(void);
static void uartPrint(const char* str);
static void uartPrintInt(int32_t value);
static void initI2CSlave(void);
static void decodeAndSetMotor(void);

int main(){
    WDT_A->CTL = WDT_A_CTL_PW | WDT_A_CTL_HOLD;
    initSystemClock();
    initUART();
    initI2CSlave();
    MC33926_Init();
    __enable_irq();
//    MC33926_SetMotor1Speed(200);
//    MC33926_SetMotor2Speed(0);
//    MC33926_SetMotor3Speed(200);
    while(1){
        //checka se il messaggio di debug è pront per stamparlo
        if(debug_ready){
           __disable_irq(); //evito race conditions
           uint8_t motor = debug_motor;
           int16_t val = debug_value;
           debug_ready = 0;
           __enable_irq();

           char debug_msg[16];
           sprintf(debug_msg,"M%d:%+d\r\n", motor, (int)val);
           uartPrint(debug_msg);
        }
        __sleep();
    }
}

static void initSystemClock(void){
    /* A 48 MHz la CPU è più veloce della Flash!
     * Si imposta Wait state = quanti cicli la CPU deve aspettare
     * Secondo la tabella a 48 MHz sono necessari 1 Wait State (WAIT_1)
     */
    FLCTL->BANK0_RDCTL &= ~FLCTL_BANK0_RDCTL_WAIT_MASK; //azzerra solo i bit del campo WAIT
    FLCTL->BANK0_RDCTL |= FLCTL_BANK0_RDCTL_WAIT_1; //imposta i bit per WAIT_1

    FLCTL->BANK1_RDCTL &= ~FLCTL_BANK1_RDCTL_WAIT_MASK; //azzerra solo i bit del campo WAIT
    FLCTL->BANK1_RDCTL |= FLCTL_BANK1_RDCTL_WAIT_1; //imposta i bit per WAIT_1
    //MSP432 ha 2 banchi di Flash (BANK0 e BANK1) per accesso alternato

    /* Configure DCO to 48MHz */
    CS->KEY = CS_KEY_VAL;                   // Unlock CS (Clock System) registers
    CS->CTL0 = CS_CTL0_DCORSEL_5;          // Set DCO to 48MHz

    /* Select DCO as source for MCLK and SMCLK with divider = 1 */
    CS->CTL1 = CS_CTL1_SELM__DCOCLK |      // MCLK = DCO   (MCLK = Master Clock (della CPU), con sorgente DCO)
               CS_CTL1_DIVM__1 |           // MCLK divider = 1
               CS_CTL1_SELS__DCOCLK |      // SMCLK = DCO  (SMCLK = SubMaster CLock (delle periferiche))
               CS_CTL1_DIVS__1;            // SMCLK divider = 1
    CS->KEY = 0;     //così non si può più modificare il clock
}

static void initUART(void){
    /* Configure UART pins P1.2 (RX) and P1.3 (TX)
     * Primary module function: SEL0 = 1, SEL1 = 0
     * P1.2= RX ; P1.3 = Tx
     */
    P1->SEL0 |= (BIT2 | BIT3);
    P1->SEL1 &= ~(BIT2 | BIT3);

    /* Put EUSCI_A0 in reset state while configuring
     * EUSCI_A0 = Enhanced Universal Serial COmmunication Interface A0
     * SWRST = Software Reset
     *  */
    EUSCI_A0->CTLW0 |= EUSCI_A_CTLW0_SWRST;

    /* Configure EUSCI_A0:
     * - EUSCI_A_CTLW0_SSEL__SMCLK: SMCLK as clock source
     * - EUSCI_A_CTLW0_SWRST: Keep in reset
     * Infatti UART ha bisogno di un clock per generare i bit rate
     */
    EUSCI_A0->CTLW0 = EUSCI_A_CTLW0_SWRST |
                      EUSCI_A_CTLW0_SSEL__SMCLK;

    /* Baud rate configuration for 115200(bit al secondo) @ 48MHz */
     EUSCI_A0->BRW = 26;                     // Clock prescaler (UCBRx)
     EUSCI_A0->MCTLW = (0xD6 << EUSCI_A_MCTLW_BRS_OFS) |  // UCBRSx = 0xD6
                         (0 << EUSCI_A_MCTLW_BRF_OFS) |      // UCBRFx = 0
                         EUSCI_A_MCTLW_OS16;                  // Oversampling mode

     /* Release from reset */
     EUSCI_A0->CTLW0 &= ~EUSCI_A_CTLW0_SWRST; //Toglie reset -> UART attiva e funzionante
}

static void uartPrint(const char * str){
    while(*str){
        //aspetta che il buffer del TX sia pronto
        while(!(EUSCI_A0->IFG & EUSCI_A_IFG_TXIFG)); //EUSCI_A_IFG_TXIFG = Transmit Interrupt Flag: 1-> buffer TX vuoto ; 0 = buffer TX pieno
        //trasmetti carattere
        EUSCI_A0->TXBUF = *str++; //TXBUF = Transmit Buffer
    }
}

static void uartPrintInt(int32_t value){
    char buffer[12];
    sprintf(buffer, "%ld", value);
    uartPrint(buffer);
}

static void initI2CSlave(void){
    /*Configure I2C pins P1.6(SDA) e P1.7 (SCL)
     * Uso funzione primaria
     */
    P1->SEL0 |= (BIT6 | BIT7);
    P1->SEL1 &= ~(BIT6 | BIT7);

    /*Metto EUSCI_B0 in reset state  mentre configro*/
    EUSCI_B0->CTLW0 = EUSCI_B_CTLW0_SWRST;

/* Configure EUSCI_B0 for I2C mode:
     * - EUSCI_B_CTLW0_MODE_3: I2C mode
     * - EUSCI_B_CTLW0_SYNC: Synchronous mode
     * - UCMST = 0 (default): Slave mode
     * - EUSCI_B_CTLW0_SSEL__SMCLK: SMCLK as clock source, non per generare SCL (quello la fa il master)
     */
    EUSCI_B0->CTLW0 = EUSCI_B_CTLW0_SWRST |
                      EUSCI_B_CTLW0_MODE_3 |
                      EUSCI_B_CTLW0_SYNC |
                      EUSCI_B_CTLW0_SSEL__SMCLK;

    /* Set own slave address (7-bit) and enable it
         * I2COA0: Own address register 0
         * I2C_SLAVE_ADDRESS = 0x10
         * UCOAEN: Own address enable
         */
     EUSCI_B0->I2COA0 = I2C_SLAVE_ADDRESS | EUSCI_B_I2COA0_OAEN;

     /* Release from reset */
     EUSCI_B0->CTLW0 &= ~EUSCI_B_CTLW0_SWRST;

     /* Enable I2C interrupts:
          * - RXIE0: Receive interrupt enable, si attiva quando arriva un byte dal master
          * - STPIE: Stop condition interrupt enable, si attiva quando master invia STOP I2c
          * - STTIE: Start condition interrupt enable (for reliable transaction detection), quando master invia START I2C
      */
     EUSCI_B0->IE |= EUSCI_B_IE_RXIE0 | EUSCI_B_IE_STPIE | EUSCI_B_IE_STTIE;
     /* Enable EUSCI_B0 interrupt in NVIC */
     NVIC_EnableIRQ(EUSCIB0_IRQn);
     //Setto priorità I2C a 2. Priorità 0 e 1 riservata per emergenze critiche e timer critici
     NVIC_SetPriority(EUSCIB0_IRQn, 2);
}

static void decodeAndSetMotor(void){
    int16_t motor_speed = value;
    if(n_motore==0 || n_motore==1 || n_motore == 2){
        motor_speed = value*4;  //Perchè il raspberry può mandare un solo byte --> da -128 a +127
    }

    if(n_motore == 0){
        MC33926_SetMotor1Speed(motor_speed);
    }
    else if(n_motore == 1){
        MC33926_SetMotor2Speed(motor_speed);
    }
    else if(n_motore == 2){
        MC33926_SetMotor3Speed(motor_speed);
    }
    else if(n_motore == 3){
        MC33926_SetMotor4Speed(value);  // pompa: no *4, qualsiasi valore != 0 accende
    }
}

/*Dal rasperry mi arriveranno 2 byte:
 * uno è il numero del motore
 * uno è il valore della velocità
 */
void EUSCIB0_IRQHandler(void){
    /*IFG = Interrupt Flag Register
     *  Bit 0 (RXIFG0):  Byte ricevuto
        Bit 4 (TXIFG0):  Pronto a trasmettere (non usato qui, siamo solo slave RX)
        Bit 6 (STTIFG):  START condition rilevata
        Bit 7 (STPIFG):  STOP condition rilevata
     */
    uint16_t status = EUSCI_B0->IFG;
    if(status & EUSCI_B_IFG_RXIFG0){
        //leggo dati ricevuti dal RX buffer
        uint8_t received_byte = EUSCI_B0->RXBUF; //Leggere RXBUF cancella automaticamente RXIFG
        if (byte_count ==0){
            n_motore = received_byte;
            byte_count=1;
        }
        else if(byte_count == 1){
            value = (int8_t)received_byte; //casto a intero perchè vogliamo segno
            decodeAndSetMotor();
            /* Set flag for deferred UART debug printing (non-blocking) */
            debug_motor = n_motore;
            debug_value = value;
            debug_ready = 1;

            byte_count=0;
        }
    }
    /* Start condition interrupt -reset state per nuova transazione*/
    if(status & EUSCI_B_IFG_STTIFG){
        EUSCI_B0->IFG &= ~EUSCI_B_IFG_STTIFG;
        //riazzero byte count perchè magari era rimasto a 1 e poi è accaduto un errore, cavo staccato ecc..
        byte_count=0;
    }
    /*Stop condition interrupt*/
    if(status & EUSCI_B_IFG_STPIFG){
        EUSCI_B0->IFG &= ~EUSCI_B_IFG_STPIFG;
        byte_count=0;
    }
}





















