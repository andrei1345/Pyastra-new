############################################################################
# $Id: 16c558.py 70 2004-08-23 01:34:19Z estyler $
#
# Description: PIC 16C558 definition. Pyastra project.
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

hdikt={'RP1': 0x6, 'PCLATH': 0xa, 'T0IF': 0x2,
       'T0IE': 0x5, 'PCON': 0x8e, 'NOT_PD': 0x3,
       'DC': 0x1, 'FSR': 0x4, 'NOT_TO': 0x4,
       'INTCON': 0xb, 'PCL': 0x2, 'PS2': 0x2,
       'PS0': 0x0, 'PS1': 0x1, 'T0SE': 0x4,
       'NOT_RBPU': 0x7, 'STATUS': 0x3, 'RP0': 0x5,
       'C': 0x0, 'INTF': 0x1, 'IRP': 0x7,
       'TRISB': 0x86, 'TRISA': 0x85, 'PORTB': 0x6,
       'PORTA': 0x5, 'GIE': 0x7, 'INTEDG': 0x6,
       'Z': 0x2, 'NOT_POR': 0x1, 'T0CS': 0x5,
       'INTE': 0x4, 'PSA': 0x3, 'OPTION_REG': 0x81,
       'INDF': 0x0, 'TMR0': 0x1, 'RBIF': 0x0,
       'RBIE': 0x3, }

pages=((0x5, 0x7FF), )

banks=((0x20, 0x7F), (0xA0, 0xBF), )

shareb=(
)

vectors=(0x0, 0x4)
maxram = 0xbf