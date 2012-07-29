/* 
 * Relays controller firmware.
 */

#define _XTAL_FREQ 16000000

#define __PICCPRO__
#include <htc.h>
#include "usart.h"

__CONFIG(FCMEN_OFF & IESO_OFF & CLKOUTEN_OFF & BOREN_ON & CP_OFF & MCLRE_ON &
        PWRTE_OFF & WDTE_OFF & FOSC_INTOSC);
__CONFIG(WRT_OFF & VCAPEN_OFF & STVREN_ON & BORV_HI & LPBOR_OFF & LVP_OFF);

typedef char *char_ptr;

const char_ptr relayPort[30] = {
    // Relay 1
    &LATA,
    &LATB,
    &LATA,
    &LATB,
    &LATE,
    &LATD,
    &LATC,
    &LATC,
    &LATC,
    &LATD,
    // Relay 11
    &LATA,
    &LATB,
    &LATA,
    &LATB,
    &LATE,
    &LATD,
    &LATA,
    &LATC,
    &LATC,
    &LATD,
    // Relay 21
    &LATA,
    &LATB,
    &LATA,
    &LATB,
    &LATE,
    &LATD,
    &LATA,
    &LATD,
    &LATC,
    &LATD
};

const char relayMask[30] = {
    // Relay 1
    4,
    8,
    32,
    1,
    4,
    32,
    1,
    16,
    8,
    2,
    // Relay 11
    2,
    16,
    16,
    2,
    2,
    64,
    64,
    32,
    4,
    1,
    // Relay 21
    1,
    32,
    8,
    4,
    1,
    128,
    128,
    16,
    2,
    8
};

char relayState[4] = {0, 0, 0, 0};

void interrupt isr()
{
    while (RCIF) {
        usart_recv();
    }
}

/*
 Apply relayState to real devices
 */
void relay_update()
{
    for (char c = 0; c < 30; c++) {
        char *port = relayPort[c];
        char mask = relayMask[c];
        if ((relayState[c / 8] & (1 << (c & 7))) != 0)
            *port |= mask;
        else
            *port &=  ~mask;
    }
}

void usart_pkt_received(unsigned char cmd, unsigned char len)
{
    switch (cmd) {
        case 'E':
            usart_pkt_send('E', 2);
            usart_pkt_put(1);
            break;
        case 'R':
            if (len == 5) {
                for (char i = 0; i < 4; i++) {
                    relayState[i] = usart_pkt_get();
                }
                relay_update();
                usart_pkt_send('R', 1);
            }
            break;
    }
}

void ports_init()
{
    ANSELA = 0;
    TRISA = 0;
    ANSELB = 0;
    TRISB = 0xc0;
    ANSELC = 0;
    TRISC = 0x80;
    ANSELD = 0;
    TRISD = 0;
    ANSELE = 0;
    TRISE = 0xf8;
    LATA = 0;
    LATB = 0;
    LATC = 0;
    LATD = 0;
    LATE = 0;
}

void main()
{
    di();
    OSCCON = 0x78;
    ports_init();
    usart_init();
    ei();
    usart_pkt_send('R', 1);
    while (1) {
        usart_check();
    }
}

