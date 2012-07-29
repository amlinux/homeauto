/* 
 * Relays controller firmware.
 */

#define _XTAL_FREQ 16000000

#define __PICCPRO__
#include <htc.h>
#include "../homeauto_relays.X/usart.h"

__CONFIG(FCMEN_OFF & IESO_OFF & CLKOUTEN_OFF & BOREN_ON & CP_OFF & MCLRE_ON &
        PWRTE_OFF & WDTE_OFF & FOSC_INTOSC);
__CONFIG(WRT_OFF & VCAPEN_OFF & STVREN_ON & BORV_HI & LPBOR_OFF & LVP_OFF);

typedef char *char_ptr;

void interrupt isr()
{
    while (RCIF) {
        usart_recv();
    }
}

void usart_pkt_received(unsigned char cmd, unsigned char len)
{
    switch (cmd) {
        case 'E':
            usart_pkt_send('E', 2);
            usart_pkt_put(2);
            break;
    }
}

void ports_init()
{
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

