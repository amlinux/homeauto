/*
 * MicroLAN protocol implementation
 */

#define _XTAL_FREQ 16000000
#include <htc.h>
#include "microlan.h"

typedef volatile unsigned char *char_ptr;
unsigned char microlan_crc;

const char_ptr uLanPort[3] = {
    &PORTC,
    &PORTD,
    &PORTD
};

const char_ptr uLanTris[3] = {
    &TRISC,
    &TRISD,
    &TRISD
};

const char uLanMask[3] = {
    16,
    8,
    4
};

void microlan_init()
{
    ANSELC &= ~0x10;
    ANSELD &= ~0x0c;
    TRISC |= 0x10;
    TRISD |= 0x0c;
    LATC &= ~0x10;
    LATD &= ~0x0c;
}

void microlan_crc_update(char dataBit)
{
    if ((microlan_crc & 1) == dataBit) {
        microlan_crc >>= 1;
    } else {
        microlan_crc = ((microlan_crc ^ 0x18) >> 1) | 0x80;
    }
}

char microlan_reset(char line)
{
    /*
     * Timer 0 prescaler = 1:4
     * Tick interval = 1 uS
     * Full timer overflow = 256 uS
     */
    OPTION_REG = (OPTION_REG & 0xc0) | 0x01;
    char_ptr tris = uLanTris[line];
    char mask = uLanMask[line];
    *tris &= ~mask;
    __delay_us(500);
    di();
    *tris |= mask;
    __delay_us(10);
    // Timeout 100 uS waiting for presence
    TMR0 = -100;
    T0IF = 0;
    char_ptr port = uLanPort[line];
    char mask = uLanMask[line];
    while ((*port & mask) != 0) {
        if (T0IF) {
            ei();
            return 0;
        }
    }
    ei();
    // Timeout 256 uS waiting for presence end
    TMR0 = -256;
    T0IF = 0;
    while ((*port & mask) == 0) {
        if (T0IF) {
            // Interrupt may occur between while() and if().
            // To avoid wrong timeout, reread the port
            if ((*port & mask) == 0) {
                return 0;
            }
        }
    }
    // Presence OK
    __delay_us(500);
    microlan_crc = 0;
    return 1;
}

void microlan_send(char line, unsigned char data)
{
    char_ptr tris = uLanTris[line];
    char mask = uLanMask[line];
    for (char c = 0; c < 8; c++) {
        di();
        if ((data & 1) != 0) {
            *tris &= ~mask;
            __delay_us(5);
            *tris |= mask;
            ei();
            __delay_us(50);
            microlan_crc_update(1);
        } else {
            *tris &= ~mask;
            __delay_us(60);
            *tris |= mask;
            ei();
            microlan_crc_update(0);
        }
        data >>= 1;
    }
}

char microlan_recv(char line, unsigned char *data)
{
    char_ptr port = uLanPort[line];
    char_ptr tris = uLanTris[line];
    char mask = uLanMask[line];
    for (char c = 0; c < 8; c++) {
        di();
        *tris &= ~mask;
        __delay_us(5);
        *tris |= mask;
        __delay_us(10);
        unsigned char readBit = ((*port & mask) == 0) ? 0 : 0x80;
        ei();
        *data = (*data >> 1) | readBit;
        if (readBit == 0) {
            // Timeout 100 uS waiting for pull-down end
            TMR0 = -100;
            T0IF = 0;
            while ((*port & mask) == 0) {
                if (T0IF) {
                    // Interrupt may occur between while() and if().
                    // To avoid wrong timeout, reread the port
                    if ((*port & mask) == 0) {
                        return 0;
                    }
                }
            }
            microlan_crc_update(0);
        } else {
            microlan_crc_update(1);
        }
    }
    return 1;
}

unsigned char microlan_search_bit(char line, char data)
{
    char_ptr port = uLanPort[line];
    char_ptr tris = uLanTris[line];
    char mask = uLanMask[line];
    // Read bit 0
    di();
    *tris &= ~mask;
    __delay_us(5);
    *tris |= mask;
    __delay_us(10);
    unsigned char bit0 = ((*port & mask) == 0) ? 0 : 1;
    ei();
    if (bit0 == 0) {
        // Timeout 100 uS waiting for pull-down end
        TMR0 = -100;
        T0IF = 0;
        while ((*port & mask) == 0) {
            if (T0IF) {
                // Interrupt may occur between while() and if().
                // To avoid wrong timeout, reread the port
                if ((*port & mask) == 0) {
                    return 0xff;
                }
            }
        }
    }
    __delay_us(50);
    // Read bit 1
    di();
    *tris &= ~mask;
    __delay_us(5);
    *tris |= mask;
    __delay_us(10);
    unsigned char bit1 = ((*port & mask) == 0) ? 0 : 1;
    ei();
    if (bit1 == 0) {
        // Timeout 100 uS waiting for pull-down end
        TMR0 = -100;
        T0IF = 0;
        while ((*port & mask) == 0) {
            if (T0IF) {
                // Interrupt may occur between while() and if().
                // To avoid wrong timeout, reread the port
                if ((*port & mask) == 0) {
                    return 0xff;
                }
            }
        }
    }
    __delay_us(50);
    // Change select bit if all devices report the same value
    if (bit0 == 0 && bit1 == 1)
        data = 0;
    else if (bit0 == 1 && bit1 == 0)
        data = 1;
    // Send select bit
    di();
    if (data != 0) {
        *tris &= ~mask;
        __delay_us(5);
        *tris |= mask;
        ei();
        __delay_us(50);
    } else {
        *tris &= ~mask;
        __delay_us(60);
        *tris |= mask;
        ei();
    }
    // Calculate response
    if (bit0 == 0)
        if (bit1 == 0)
            return 2;
        else
            return 0;
    else
        if (bit1 == 0)
            return 1;
        else
            return 3;
}