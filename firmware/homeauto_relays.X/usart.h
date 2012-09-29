#ifndef USART_H
#define USART_H

/* Initialize USART */
void usart_init();

/* Call this often to check for pending received packets */
void usart_check();

/* Call this function when data are waiting for being read */
void usart_recv();

/* Call this function when USART output buffer emptied to fit the next byte */
void usart_send();

/* This function is callback. It must be defined in user code.
 * When packet is received completely the library will call
 * usart_pkt_received(). User code can execute: usart_pkt_get()
 * to get cmd args */
void usart_pkt_received(unsigned char cmd, unsigned char len);
unsigned char usart_pkt_get();

/* Send packet asynchronously */
void usart_pkt_send(unsigned char cmd, unsigned char len);
void usart_pkt_put(unsigned char data);

/* Check whether output queue is empty */
unsigned char usart_send_empty();

/* Call 1 time per second to make timeouts work */
void usart_1sec_timer();

#endif