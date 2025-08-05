############################################################################
# $Id: 16c923.py 70 2004-08-23 01:34:19Z estyler $
#
# Description: PIC 16C923 definition. Pyastra project.
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

hdikt={'NOT_T1SYNC': 0x2, 'BF': 0x0, 'LMUX1': 0x1,
       'CKP': 0x4, 'T2CON': 0x12, 'T1CON': 0x10,
       'PSPMODE': 0x4, 'T0SE': 0x4, 'NOT_POR': 0x1,
       'LP3': 0x3, 'LP2': 0x2, 'LP1': 0x1,
       'LP0': 0x0, 'PIE1': 0x8c, 'TMR1ON': 0x0,
       'D': 0x5, 'PORTF': 0x107, 'PORTG': 0x108,
       'PORTD': 0x8, 'PORTE': 0x9, 'PORTB': 0x6,
       'PORTC': 0x7, 'PORTA': 0x5, 'P': 0x4,
       'GIE': 0x7, 'NOT_A': 0x5, 'PR2': 0x92,
       'INTEDG': 0x6, 'LCDIF': 0x7, 'SSPBUF': 0x13,
       'SLPEN': 0x6, 'STATUS': 0x3, 'PEIE': 0x6,
       'SSPIE': 0x3, 'SSPIF': 0x3, 'T2CKPS0': 0x0,
       'T2CKPS1': 0x1, 'INTCON': 0xb, 'VGEN': 0x4,
       'PCL': 0x2, 'PS2': 0x2, 'PS0': 0x0,
       'TMR1H': 0xf, 'TMR1L': 0xe, 'CCP1M2': 0x2,
       'CCP1M3': 0x3, 'CCP1M0': 0x0, 'CCP1M1': 0x1,
       'TMR1CS': 0x1, 'IRP': 0x7, 'LCDCON': 0x10f,
       'NOT_RBPU': 0x7, 'I2C_STOP': 0x4, 'CS1': 0x3,
       'CS0': 0x2, 'C': 0x0, 'TRISC': 0x87,
       'TRISB': 0x86, 'TRISA': 0x85, 'TRISG': 0x188,
       'TRISF': 0x187, 'TRISE': 0x89, 'TRISD': 0x88,
       'OPTION_REG': 0x81, 'LCDIE': 0x7, 'DATA_ADDRESS': 0x5,
       'PIR1': 0xc, 'LCDPS': 0x10e, 'INTE': 0x4,
       'LCDD12': 0x11c, 'LCDD13': 0x11d, 'LCDD10': 0x11a,
       'LCDD11': 0x11b, 'S': 0x3, 'LCDD14': 0x11e,
       'LCDD15': 0x11f, 'T0CS': 0x5, 'UA': 0x1,
       'RBIF': 0x0, 'RBIE': 0x3, 'T1OSCEN': 0x3,
       'R_W': 0x2, 'LMUX0': 0x0, 'PCLATH': 0xa,
       'SSPSTAT': 0x94, 'PCON': 0x8e, 'TOUTPS2': 0x5,
       'TOUTPS3': 0x6, 'TOUTPS0': 0x3, 'TOUTPS1': 0x4,
       'FSR': 0x4, 'TRISE2': 0x2, 'TRISE1': 0x1,
       'TRISE0': 0x0, 'NOT_W': 0x2, 'SSPOV': 0x6,
       'T0IF': 0x2, 'LCDD09': 0x119, 'LCDD08': 0x118,
       'CCP1CON': 0x17, 'LCDD01': 0x111, 'LCDD00': 0x110,
       'LCDD03': 0x113, 'LCDD02': 0x112, 'LCDD05': 0x115,
       'LCDD04': 0x114, 'LCDD07': 0x117, 'LCDD06': 0x116,
       'TMR1IE': 0x0, 'SE12': 0x3, 'D_A': 0x5,
       'SE16': 0x4, 'INTF': 0x1, 'SE5': 0x1,
       'SE0': 0x0, 'OBF': 0x6, 'TMR2IE': 0x1,
       'TMR2IF': 0x1, 'R': 0x2, 'Z': 0x2,
       'NOT_WRITE': 0x2, 'SE27': 0x6, 'SE20': 0x5,
       'SSPADD': 0x93, 'SE29': 0x7, 'NOT_TO': 0x4,
       'SSPCON': 0x14, 'TMR2': 0x11, 'TMR0': 0x1,
       'LCDSE': 0x10d, 'CCPR1L': 0x15, 'READ_WRITE': 0x2,
       'PSA': 0x3, 'CCPR1H': 0x16, 'T0IE': 0x5,
       'NOT_PD': 0x3, 'DC': 0x1, 'IBF': 0x7,
       'I2C_READ': 0x2, 'PS1': 0x1, 'SSPEN': 0x5,
       'WCOL': 0x7, 'RP1': 0x6, 'RP0': 0x5,
       'T1CKPS1': 0x5, 'T1CKPS0': 0x4, 'CCP1IF': 0x2,
       'LCDEN': 0x7, 'CCP1IE': 0x2, 'CCP1X': 0x5,
       'CCP1Y': 0x4, 'SE9': 0x2, 'TMR2ON': 0x2,
       'TMR1IF': 0x0, 'IBOV': 0x5, 'SSPM0': 0x0,
       'SSPM1': 0x1, 'SSPM2': 0x2, 'SSPM3': 0x3,
       'I2C_START': 0x3, 'NOT_ADDRESS': 0x5, 'INDF': 0x0,
       'I2C_DATA': 0x5, }

pages=((0x5, 0x7FF), (0x800, 0xFFF), )

banks=((0x20, 0x6F), (0x70, 0x7F), (0xA0, 0xEF), )

shareb=(
        ((0x70, 0x7F), (0xF0, 0xFF), (0x170, 0x17F), (0x1F0, 0x1FF), ),
)

vectors=(0x0, 0x4)
maxram = 0x1ff