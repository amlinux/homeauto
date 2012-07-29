#include "crc.h"

void calc_crc(unsigned char *crc, unsigned char data)
{
    char i;
    for (i = 0; i < 8; i++) {
        if ((*crc ^ data) & 1)
            *crc ^= 0x9d;
        *crc >>= 1;
        data >>= 1;
    }
}