############################################################################
# $Id: 16f870i.py 95 2004-11-28 18:50:38Z estyler $
#
# Description: PIC 16F870I definition. Pyastra project.
# Author: Alex Ziranov <estyler _at_ users _dot_ sourceforge _dot_ net>
#    
# Copyright (c) 2004 Alex Ziranov.  All rights reserved.
#
############################################################################
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
############################################################################

hdikt={'RCIF': 0x5, 'NOT_T1SYNC': 0x2, 'RCIE': 0x5,
       'WR': 0x1, 'T2CON': 0x12, 'T1CON': 0x10,
       'T0SE': 0x4, 'SPBRG': 0x99, 'RD': 0x0,
       'PCFG3': 0x3, 'PCFG2': 0x2, 'PCFG1': 0x1,
       'PCFG0': 0x0, 'PIE2': 0x8d, 'PIE1': 0x8c,
       'TMR1ON': 0x0, 'TRMT': 0x1, 'PORTB': 0x6,
       'PORTC': 0x7, 'PORTA': 0x5, 'GIE': 0x7,
       'PR2': 0x92, 'GO': 0x2, 'INTEDG': 0x6,
       'WRERR': 0x3, 'T0CS': 0x5, 'ADRESL': 0x9e,
       'EECON1': 0x18c, 'EECON2': 0x18d, 'ADRESH': 0x1e,
       'TXIF': 0x4, 'TXIE': 0x4, 'SPEN': 0x7,
       'TXSTA': 0x98, 'INTE': 0x4, 'PEIE': 0x6,
       'T1SYNC': 0x2, 'WREN': 0x2, 'SYNC': 0x4,
       'T2CKPS0': 0x0, 'T2CKPS1': 0x1, 'INTCON': 0xb,
       'NOT_DONE': 0x2, 'PCL': 0x2, 'PS2': 0x2,
       'ADON': 0x0, 'PS0': 0x0, 'TMR1H': 0xf,
       'TMR1L': 0xe, 'CCP1M2': 0x2, 'CCP1M3': 0x3,
       'CCP1M0': 0x0, 'CCP1M1': 0x1, 'ADDEN': 0x3,
       'TMR1CS': 0x1, 'CCP1IF': 0x2, 'NOT_RBPU': 0x7,
       'C': 0x0, 'CHS0': 0x3, 'CHS1': 0x4,
       'CHS2': 0x5, 'TRISC': 0x87, 'TRISB': 0x86,
       'TRISA': 0x85, 'ADCON1': 0x9f, 'ADCON0': 0x1f,
       'OPTION_REG': 0x81, 'PIR2': 0xd, 'PIR1': 0xc,
       'OERR': 0x1, 'RP1': 0x6, 'PSA': 0x3,
       'ADFM': 0x7, 'CREN': 0x4, 'RBIF': 0x0,
       'RBIE': 0x3, 'TXREG': 0x19, 'T1OSCEN': 0x3,
       'PCLATH': 0xa, 'PCON': 0x8e, 'TOUTPS2': 0x5,
       'TOUTPS3': 0x6, 'TOUTPS0': 0x3, 'TOUTPS1': 0x4,
       'FSR': 0x4, 'RX9D': 0x0, 'T0IF': 0x2,
       'RX9': 0x6, 'CCP1CON': 0x17, 'RCREG': 0x1a,
       'EEDATH': 0x10e, 'EEDATA': 0x10c, 'EEADRH': 0x10f,
       'TMR2IE': 0x1, 'TMR2IF': 0x1, 'NOT_BO': 0x0,
       'ADIE': 0x6, 'ADIF': 0x6, 'Z': 0x2,
       'T1CKPS0': 0x4, 'TXEN': 0x5, 'NOT_TO': 0x4,
       'TMR2': 0x11, 'TMR0': 0x1, 'BRGH': 0x2,
       'CCPR1L': 0x15, 'CCPR1H': 0x16, 'T0IE': 0x5,
       'ADCS1': 0x7, 'NOT_PD': 0x3, 'DC': 0x1,
       'NOT_BOR': 0x0, 'FERR': 0x2, 'RCSTA': 0x18,
       'EEADR': 0x10d, 'PS1': 0x1, 'ADCS0': 0x6,
       'GO_DONE': 0x2, 'STATUS': 0x3, 'RP0': 0x5,
       'T1CKPS1': 0x5, 'INTF': 0x1, 'EEPGD': 0x7,
       'IRP': 0x7, 'CCP1IE': 0x2, 'CCP1X': 0x5,
       'CCP1Y': 0x4, 'SREN': 0x5, 'CSRC': 0x7,
       'TX9': 0x6, 'TMR2ON': 0x2, 'TMR1IF': 0x0,
       'TMR1IE': 0x0, 'INDF': 0x0, 'NOT_POR': 0x1,
       'TX9D': 0x0, }

pages=((0x5, 0x6FF), )

banks=((0x20, 0x6F), (0x71, 0x7F), (0xA0, 0xB4), )

shareb=(
        ((0x20, 0x6F), (0x120, 0x16F), ),
        ((0xA0, 0xB4), (0x1A0, 0x1B4), ),
        ((0x71, 0x7F), (0xF1, 0xFF), (0x171, 0x17F), (0x1F1, 0x1FF), ),
)

vectors=(0x0, 0x4)
maxram = 0x1ff