/*
 * Reading buttons
 */

#define _XTAL_FREQ 16000000
#include <htc.h>
#include "buttons.h"
#include "../homeauto_relays.X/usart.h"

typedef volatile unsigned char *char_ptr;

#define BUTTONS 28

const char_ptr btnPort[BUTTONS] = {
    // BTN11
    &PORTA,
    &PORTA,
    &PORTA,
    &PORTA,
    &PORTA,
    &PORTA,
    &PORTE,
    // BTN21
    &PORTE,
    &PORTE,
    &PORTA,
    &PORTA,
    // BTN31
    &PORTC,
    &PORTC,
    &PORTC,
    &PORTC,
    &PORTD,
    &PORTD,
    // BTN41
    &PORTD,
    &PORTD,
    &PORTD,
    &PORTC,
    // BTN51
    &PORTB,
    &PORTB,
    &PORTB,
    &PORTB,
    &PORTB,
    &PORTB,
    &PORTD
};

const char_ptr btnTris[BUTTONS] = {
    // BTN11
    &TRISA,
    &TRISA,
    &TRISA,
    &TRISA,
    &TRISA,
    &TRISA,
    &TRISE,
    // BTN21
    &TRISE,
    &TRISE,
    &TRISA,
    &TRISA,
    // BTN31
    &TRISC,
    &TRISC,
    &TRISC,
    &TRISC,
    &TRISD,
    &TRISD,
    // BTN41
    &TRISD,
    &TRISD,
    &TRISD,
    &TRISC,
    // BTN51
    &TRISB,
    &TRISB,
    &TRISB,
    &TRISB,
    &TRISB,
    &TRISB,
    &TRISD
};

const char btnMask[BUTTONS] = {
    // BTN11
    1,
    2,
    4,
    8,
    16,
    32,
    1,
    // BTN21
    2,
    4,
    128,
    64,
    // BTN31
    1,
    2,
    4,
    8,
    1,
    2,
    // BTN41
    64,
    32,
    16,
    32,
    // BTN51
    32,
    16,
    8,
    4,
    2,
    1,
    128
};

// Buttons state
// s... .ccc
// s - last steady state (1 pressed, 0 unpressed)
// ccc - counter for jitter protection
unsigned char btnState[BUTTONS] = {0};

// Button keypress length
unsigned short btnDuration[BUTTONS];

void buttons_init()
{
    ANSELA = 0;
    TRISA = 0xff;
    ANSELB = 0;
    TRISB = 0xff;
    ANSELC &= ~0x2f;
    TRISC |= 0x2f;
    ANSELD &= ~0xf3;
    TRISD |= 0xf3;
    ANSELE &= ~0x07;
    TRISE |= 0x07;
    /* LFINTOSC (32768 Hz) divided by 1:1 */
    T1CON = 0xc7;
    T1GCON = 0;
    TMR1IE = 1;
    PEIE = 1;
}

void buttons_isr()
{
    if (TMR1IF) {
        // Usually this event happens 128 times per second
        // (perios is about 7.8ms)
        TMR1IF = 0;
        unsigned char ticks = TMR1H;
        TMR1H = 0xff;
        if (ticks < 0xff)
            ticks++;
        // If some of ticks were missed, they are
        // counted in ticks variable
        for (char c = 0; c < BUTTONS; c++) {
            char_ptr port = btnPort[c];
            unsigned char mask = btnMask[c];
            unsigned char newState = ((*port & mask) == 0) ? 128 : 0;
            unsigned char *state = btnState + c;
            if ((*state & 128) != newState) {
                if (((++*state) & 4) != 0) {
                    // New steady state
                    *state = newState;
                    // Report new state to the host
                    if (newState != 0) {
                        // Button press
                        usart_pkt_send('B', 3);
                        usart_pkt_put(1);
                        usart_pkt_put(c);
                    } else {
                        // Button release
                        usart_pkt_send('B', 5);
                        usart_pkt_put(0);
                        usart_pkt_put(c);
                        usart_pkt_put(btnDuration[c] >> 8);
                        usart_pkt_put(btnDuration[c]);
                    }
                    btnDuration[c] = 0;
                }
            } else {
                // Reset jitter detect counter
                *state &= 128;
                // If button is pressed increment duration counters
                if (newState != 0) {
                    unsigned short cnt = ++btnDuration[c];
                    // Timer overflow
                    if (cnt == 0) {
                        btnDuration[c] = 0xffff;
                        return;
                    }
                    // 1 second time marks
                    if ((cnt & 127) == 0 && (cnt <= 10 * 128)) {
                        usart_pkt_send('B', 4);
                        usart_pkt_put(2);
                        usart_pkt_put(c);
                        usart_pkt_put(cnt >> 7);
                    }
                }
            }
        }
    }
}
