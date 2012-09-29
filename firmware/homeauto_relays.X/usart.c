#include <htc.h>
#include "usart.h"
#include "crc.h"

/*
 * Packet format
 * -------------
 * 0x5a - start signature
 * len - packet length (cmd+args)
 * cmd - command
 * ... args ...
 * CRC
 */

// Timeout in seconds before resetting baudrate */
#define USART_TIMEOUT 10

// must be power of 2
#define BUFSIZE 64

/* Receive buffer */
unsigned char usart_rbuf[BUFSIZE];
// Position where packet being received starts
unsigned char usart_rbuf_wbegin = 0;
// Write pointer
unsigned char usart_rbuf_wptr = 0;
// Read pointer
unsigned char usart_rbuf_rptr = 0;
// Packet being received
unsigned char usart_rcv_state = 0;
unsigned char usart_rcv_len;
unsigned char usart_rcv_crc;

/* Send buffer */
unsigned char usart_wbuf[BUFSIZE];
// Write position
unsigned char usart_wbuf_wptr = 0;
// Read position
unsigned char usart_wbuf_rptr = 0;
// Packet being sent
unsigned char usart_snd_aborted;
unsigned char usart_snd_len;
unsigned char usart_snd_crc;

/* Counters */
unsigned char usart_framing_errors = 0;
unsigned char usart_overrun_errors = 0;
unsigned char usart_rbuf_overflow_errors = 0;
unsigned char usart_wbuf_overflow_errors = 0;
unsigned char usart_internal_errors = 0;
unsigned char calc_crc_errors = 0;
unsigned char usart_read_overflow_errors = 0;
unsigned char usart_write_overflow_errors = 0;
unsigned char usart_calibration_errors = 0;

/* Packet receive timeout */
unsigned char usart_timeout = 0;
unsigned char calibrated;

void usart_init()
{
    ANSELC &= ~0xc0;
    TRISC &= ~0x40;
    TXSTA = 0x24;
    RCSTA = 0x90;
    BAUDCON = 0x08;
    SPBRGH = 0;
    SPBRGL = 207;
    RCIE = 1;
    PEIE = 1;
    calibrated = 0;
}

void usart_rbuf_store(unsigned char data)
{
    usart_rbuf[usart_rbuf_wptr] = data;
    usart_rbuf_wptr = (usart_rbuf_wptr + 1) & (BUFSIZE - 1);
}

char usart_check_errors()
{
    char errors = 0;
    if (FERR) {
        while (FERR)
            RCREG;
        usart_rbuf_wptr = usart_rbuf_wbegin;
        usart_rcv_state = 0;
        usart_framing_errors++;
        errors = 1;
    }
    if (OERR) {
        CREN = 0;
        CREN = 1;
        usart_rbuf_wptr = usart_rbuf_wbegin;
        usart_rcv_state = 0;
        usart_overrun_errors++;
        errors = 1;
    }
    return errors;
}

void usart_recv()
{
    unsigned char data;
    if (usart_check_errors())
        return;
    data = RCREG;
    switch (usart_rcv_state) {
        case 0:
            // packet header
            if (data == 0x5a)
                usart_rcv_state = 1;
            break;
        case 1:
            // packet length
            usart_rcv_len = data;
            // length of unclaimed data
            unsigned char unclaimed = usart_rbuf_wptr - usart_rbuf_rptr;
            if (unclaimed >= BUFSIZE)
                unclaimed += BUFSIZE;
            // buffer overflow condition
            if (data == 0 || data + unclaimed + 1 >= BUFSIZE - 1) {
                // overflow
                usart_rbuf_overflow_errors++;
                usart_rcv_state = 0;
            } else {
                // enough space
                usart_rcv_state = 2;
                usart_rcv_crc = 0;
                // storing length in the buffer
                usart_rbuf_store(usart_rcv_len);
                // accumulating CRC
                calc_crc(&usart_rcv_crc, usart_rcv_len);
            }
            break;
        case 2:
            // accumulating CRC
            calc_crc(&usart_rcv_crc, data);
            // storing data in the buffer
            usart_rbuf_store(data);
            if (--usart_rcv_len == 0)
                usart_rcv_state = 3;
            break;
        case 3:
            // accumulating CRC
            calc_crc(&usart_rcv_crc, data);
            // checking CRC
            if (usart_rcv_crc == 0) {
                // packet received successfully
                // on the next usart_check() call callback
                // will be triggered
                usart_rbuf_wbegin = usart_rbuf_wptr;
                usart_rcv_state = 0;
                usart_timeout = 0;
            } else {
                // CRC error
                calc_crc_errors++;
                usart_rbuf_wptr = usart_rbuf_wbegin;
                usart_rcv_state = 0;
            }
            break;
        default:
            usart_internal_errors++;
    }
}

void usart_check()
{
    unsigned char watchdog, error;
    usart_check_errors();
    // check for unclaimed received packets
    if (usart_rbuf_rptr != usart_rbuf_wbegin) {
        unsigned char next_rptr, len, cmd;
        len = usart_pkt_get();
        next_rptr = (usart_rbuf_rptr + len) & (BUFSIZE - 1);
        cmd = usart_pkt_get();
        switch (cmd) {
            case 0xf0:
                // auto baud-rate calibration
                di();
                // clearing receiver FIFO
                while (RCIF)
                    RCREG;
                ABDEN = 1;
                // timeout 16ms
                OPTION_REG = (OPTION_REG & 0xc0) | 0x07;
                TMR0 = 0;
                T0IF = 0;
                watchdog = 0;
                error = 0;
                calibrated = 1;
                while (ABDEN) {
                    if (T0IF) {
                        usart_calibration_errors++;
                        SPBRGH = 0;
                        SPBRGL = 207;
                        error = 1;
                        calibrated = 0;
                        break;
                    }
                }
                usart_pkt_send(0xf0, 4);
                usart_pkt_put(error);
                usart_pkt_put(SPBRGH);
                usart_pkt_put(SPBRGL);
                // clearing receiver FIFO
                while (RCIF)
                    RCREG;
                ei();
                break;
            case 0xf1:
                usart_pkt_send(0xf1, 10);
                usart_pkt_put(usart_framing_errors);
                usart_pkt_put(usart_overrun_errors);
                usart_pkt_put(usart_rbuf_overflow_errors);
                usart_pkt_put(usart_wbuf_overflow_errors);
                usart_pkt_put(usart_internal_errors);
                usart_pkt_put(calc_crc_errors);
                usart_pkt_put(usart_read_overflow_errors);
                usart_pkt_put(usart_write_overflow_errors);
                usart_pkt_put(usart_calibration_errors);
                break;
            default:
                usart_pkt_received(cmd, len);
        }
        // discard unclaimed arguments
        usart_rbuf_rptr = next_rptr;
    }
    usart_send();
}

unsigned char usart_pkt_get()
{
    unsigned char data;
    if (usart_rbuf_rptr == usart_rbuf_wbegin) {
        usart_read_overflow_errors++;
        return 0;
    }
    data = usart_rbuf[usart_rbuf_rptr];
    usart_rbuf_rptr = (usart_rbuf_rptr + 1) & (BUFSIZE - 1);
    return data;
}

void usart_send()
{
    // Is USART ready to send and any data are in buffer
    while ((PIR1 & 0x10) != 0 && usart_wbuf_rptr != usart_wbuf_wptr) {
        // Sending byte
        TXREG = usart_wbuf[usart_wbuf_rptr];
        usart_wbuf_rptr = (usart_wbuf_rptr + 1) & (BUFSIZE - 1);
    }
}

void usart_pkt_send(unsigned char cmd, unsigned char len)
{
    // length of unsent data
    unsigned char unsent = usart_wbuf_wptr - usart_wbuf_rptr;
    if (unsent >= BUFSIZE)
        unsent += BUFSIZE;
    if (unsent + len + 3 >= BUFSIZE - 1) {
        usart_write_overflow_errors++;
        usart_snd_aborted = 1;
    } else {
        usart_snd_aborted = 0;
        usart_snd_len = len + 2;
        usart_pkt_put(0x5a);
        usart_snd_crc = 0;
        usart_pkt_put(len);
        usart_pkt_put(cmd);
    }
}

void usart_pkt_put(unsigned char data)
{
    unsigned char next_ptr;
    if (usart_snd_aborted) {
        usart_write_overflow_errors++;
        return;
    }
    next_ptr = (usart_wbuf_wptr + 1) & (BUFSIZE - 1);
    if (next_ptr == usart_wbuf_rptr) {
        usart_wbuf_overflow_errors++;
        usart_snd_aborted = 1;
        return;
    }
    usart_wbuf[usart_wbuf_wptr] = data;
    usart_wbuf_wptr = next_ptr;
    // accumulating CRC
    calc_crc(&usart_snd_crc, data);
    if (--usart_snd_len == 0) {
        // End of packet
        usart_snd_aborted = 1;
        next_ptr = (usart_wbuf_wptr + 1) & (BUFSIZE - 1);
        if (next_ptr == usart_wbuf_rptr) {
            usart_wbuf_overflow_errors++;
            return;
        }
        usart_wbuf[usart_wbuf_wptr] = usart_snd_crc;
        usart_wbuf_wptr = next_ptr;
    }
    usart_send();
}

unsigned char usart_send_empty()
{
    if (usart_wbuf_wptr == usart_wbuf_rptr)
        return 1;
    else
        return 0;
}

void usart_1sec_timer()
{
    if (++usart_timeout == USART_TIMEOUT) {
        SPBRGH = 0;
        SPBRGL = 207;
        calibrated = 0;
        usart_timeout = 0;
    }
    /* Every second "I'm not calibrated" error is sent */
    if (calibrated == 0)
        usart_pkt_send('R', 1);
}
