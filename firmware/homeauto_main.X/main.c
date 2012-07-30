/* 
 * Relays controller firmware.
 */

#define _XTAL_FREQ 16000000
#include <htc.h>
#include "../homeauto_relays.X/usart.h"
#include "microlan.h"

__CONFIG(FCMEN_OFF & IESO_OFF & CLKOUTEN_OFF & BOREN_ON & CP_OFF & MCLRE_ON &
        PWRTE_OFF & WDTE_OFF & FOSC_INTOSC);
__CONFIG(WRT_OFF & VCAPEN_OFF & STVREN_ON & BORV_HI & LPBOR_OFF & LVP_OFF);

// Current MicroLAN task. If it's set no other MicroLAN commands
// will be accepted.
unsigned char microlan_task = 0;
char microlan_line;
unsigned char microlan_buf[8];
unsigned char microlan_prefix_len;

#define MICROLAN_CMD_READROM 1
#define MICROLAN_CMD_SEARCHROM 2
#define MICROLAN_CMD_CONVERTT 3
#define MICROLAN_CMD_READTEMP 4

#define MICROLAN_ERROR_CMD 0xff
#define MICROLAN_ERROR_LINE 0xfe
#define MICROLAN_ERROR_RECV 0xfd
#define MICROLAN_ERROR_PRESENCE 0xfc
#define MICROLAN_ERROR_CRC 0xfb
#define MICROLAN_ERROR_SEARCH 0xfa
#define MICROLAN_ERROR_NODEVICES 0xf9

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
        case 'M':
            if (microlan_task != 0) {
                usart_pkt_send('M', 2);
                usart_pkt_put(0);
                break;
            }
            microlan_task = usart_pkt_get();
            microlan_line = usart_pkt_get();
            if (microlan_line >= 3) {
                usart_pkt_send('M', 2);
                usart_pkt_put(MICROLAN_ERROR_LINE);
                break;
            }
            switch (microlan_task) {
                case MICROLAN_CMD_READROM:
                case MICROLAN_CMD_CONVERTT:
                    break;
                case MICROLAN_CMD_READTEMP:
                    for (char c = 0; c < 8; c++)
                        microlan_buf[c] = usart_pkt_get();
                    break;
                case MICROLAN_CMD_SEARCHROM:
                    microlan_prefix_len = usart_pkt_get();
                    for (char c = 0; c < 8; c++)
                        microlan_buf[c] = usart_pkt_get();
                    break;
                default:
                    microlan_task = 0;
                    usart_pkt_send('M', 2);
                    usart_pkt_put(MICROLAN_ERROR_CMD);
            }
            break;
    }
}

void main()
{
    di();
    OSCCON = 0x78;
    microlan_init();
    usart_init();
    ei();
    usart_pkt_send('R', 1);
    while (1) {
        usart_check();
        if (microlan_task != 0) {
            char fail = 0;
            char c;
            switch (microlan_task) {
                case MICROLAN_CMD_READROM:
                    if (!microlan_reset(microlan_line)) {
                        usart_pkt_send('M', 2);
                        usart_pkt_put(MICROLAN_ERROR_PRESENCE);
                    } else {
                        microlan_send(microlan_line, 0x33);
                        microlan_crc = 0;
                        for (c = 0; c < 8; c++) {
                            if (!microlan_recv(microlan_line,
                                    &microlan_buf[c])) {
                                fail = 1;
                                break;
                            }
                        }
                        if (fail) {
                            usart_pkt_send('M', 2);
                            usart_pkt_put(MICROLAN_ERROR_RECV);
                        } else if (microlan_crc != 0) {
                            usart_pkt_send('M', 2);
                            usart_pkt_put(MICROLAN_ERROR_CRC);
                        } else {
                            usart_pkt_send('M', 10);
                            usart_pkt_put(0);
                            for (c = 0; c < 8; c++)
                                usart_pkt_put(microlan_buf[c]);
                        }
                    }
                    break;
                case MICROLAN_CMD_CONVERTT:
                    if (!microlan_reset(microlan_line)) {
                        usart_pkt_send('M', 2);
                        usart_pkt_put(MICROLAN_ERROR_PRESENCE);
                    } else {
                        microlan_send(microlan_line, 0xcc);
                        microlan_send(microlan_line, 0x44);
                        usart_pkt_send('M', 2);
                        usart_pkt_put(0);
                    }
                    break;
                case MICROLAN_CMD_READTEMP:
                    if (!microlan_reset(microlan_line)) {
                        usart_pkt_send('M', 2);
                        usart_pkt_put(MICROLAN_ERROR_PRESENCE);
                    } else {
                        microlan_send(microlan_line, 0x55);
                        for (c = 0; c < 8; c++)
                            microlan_send(microlan_line, microlan_buf[c]);
                        microlan_send(microlan_line, 0xbe);
                        microlan_crc = 0;
                        for (c = 0; c < 8; c++) {
                            if (!microlan_recv(microlan_line,
                                    &microlan_buf[c])) {
                                fail = 1;
                                break;
                            }
                        }
                        if (fail || !microlan_recv(microlan_line, &c)) {
                            usart_pkt_send('M', 2);
                            usart_pkt_put(MICROLAN_ERROR_RECV);
                        } else if (microlan_crc != 0) {
                            usart_pkt_send('M', 2);
                            usart_pkt_put(MICROLAN_ERROR_CRC);
                        } else {
                            usart_pkt_send('M', 4);
                            usart_pkt_put(0);
                            usart_pkt_put(microlan_buf[0]);
                            usart_pkt_put(microlan_buf[1]);
                        }
                    }
                    break;
                case MICROLAN_CMD_SEARCHROM:
                    if (!microlan_reset(microlan_line)) {
                        usart_pkt_send('M', 2);
                        usart_pkt_put(MICROLAN_ERROR_PRESENCE);
                    } else {
                        microlan_send(microlan_line, 0xf0);
                        for (c = 0; c < 64; c++) {
                            unsigned char *buf = &microlan_buf[c / 8];
                            unsigned char mask = (1 << (c & 7));
                            char selectBit = (*buf & mask) ? 1 : 0;
                            char dataBit = microlan_search_bit(microlan_line,
                                    selectBit);
                            if (dataBit == 0xff) {
                                // Devices hold 0 too long
                                fail = 1;
                                usart_pkt_send('M', 2);
                                usart_pkt_put(MICROLAN_ERROR_RECV);
                                break;
                            } else if (dataBit == 3) {
                                // No devices replied
                                fail = 1;
                                usart_pkt_send('M', 2);
                                usart_pkt_put(MICROLAN_ERROR_NODEVICES);
                                break;
                            } else if (c < microlan_prefix_len) {
                                // Known bit
                                if (dataBit != 2 && dataBit != selectBit) {
                                    fail = 1;
                                    usart_pkt_send('M', 2);
                                    usart_pkt_put(MICROLAN_ERROR_SEARCH);
                                    break;
                                }
                            } else if (dataBit == 2) {
                                // Bit read conflict
                                fail = 2;
                                microlan_prefix_len = c;
                                break;
                            } else {
                                *buf = (*buf & ~mask) | (dataBit ? mask : 0);
                            }
                        }
                        if (fail == 1) {
                            // Error already sent
                        } else {
                            usart_pkt_send('M', 11);
                            usart_pkt_put(0);
                            if (fail == 2)
                                usart_pkt_put(microlan_prefix_len);
                            else
                                usart_pkt_put(64);
                            for (c = 0; c < 8; c++)
                                usart_pkt_put(microlan_buf[c]);
                        }
                    }
                    break;
            }
            microlan_task = 0;
        }
    }
}

