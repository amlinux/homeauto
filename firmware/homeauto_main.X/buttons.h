#ifndef BUTTONS_H
#define BUTTONS_H

/*
 * Initialize buttons subsystem
 */
void buttons_init();

/*
 * Notify buttons subsystem about interrupt
 */
void buttons_isr();

#endif