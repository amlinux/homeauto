#ifndef MICROLAN_H
#define MICROLAN_H

extern unsigned char microlan_crc;

/* Initialize microlan */
void microlan_init();

/*
 * Send reset pulse and wait for presence pulse
 *
 * Return value:
 * 1 - success (presence pulse found)
 * 0 - failure (no presence)
 */
char microlan_reset(char line);

/*
 * Send a byte
 */
void microlan_send(char line, unsigned char data);

/*
 * Receive a byte
 * 
 * Return value:
 * 1 - success
 * 0 - failure (too long pull-down pulses)
 */
char microlan_recv(char line, unsigned char *data);

/*
 * Receive a bit during Search ROM
 *
 * data: 0 to select 0, any other value to select 1
 * Return value:
 * 1 - all devices have bit 1
 * 0 - all devices have bit 0
 * 2 - device conflict (0 vs 1)
 * 3 - no devices responding
 * 0xff - bit read error
 */
unsigned char microlan_search_bit(char line, char data);

#endif