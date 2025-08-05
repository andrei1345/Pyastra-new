############################################################################
# $Id: tree2asm.py 104 2004-12-23 21:30:35Z estyler $
#
# Description: pic14 tree to assemler convertor. Pyastra project.
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

#
# FIXME: check whether builtins return correct Z flag (for cases) or they don't
#        12f509, 16c505, 16c57, 16f57 may not work because they may have not
#        7-bit based addressing.
# TODO:
#   1. set function's starting bank as the bank of its last argument.
#   2. add 'verbatim' argument to asm function
#   3. check whether all processor definition file are ok.
#

import types, compiler, sys, os.path, pyastra.ports.pic14
from ast import *

class tree2asm:
    body=[]
    stack=-1
    dikt={}
    bank_cmds=('addwf', 'andwf', 'bcf', 'bsf', 'btfsc', 'btfss', 'clrf', 'comf', 'decf', 'decfsz', 'incf', 'incfsz', 'iorwf', 'movf', 'movwf', 'rlf', 'rrf', 'subwf', 'swapf', 'xorwf')
    cond_br_cmds=('btfsc', 'btfss', 'decfsz', 'incfsz')
    pagesel_cmds=('call', 'goto')
    no_bank_cmds=('addlw', 'andlw', 'call', 'clrw', 'clrwdt', 'goto', 'iorlw', 'movlw', 'nop', 'retfie', 'retlw', 'return', 'sleep', 'sublw', 'xorlw')
    bank_indep=('STATUS', 'FSR', 'PCLATH', 'INTCON', 'PCL')
    lbl_stack=[]
    label=-1
    funcs={}
    asm=0
    error='Error'
    warning='Warning'
    message='Message'
    ram_usage=1
    infunc=0
    curr_bank=-1
    del_last=0
    last_bank=prelast_bank=-1
    interr = ''
    interr_instr = 0
    in_inter = 0
    inter_ret=''
    last_instr=0
    prelast_instr=0
    cur_page=0
    
    def __init__(self, ICD, op_speed, PROC, say):
        self.ICD=ICD
        self.op_speed=op_speed
        self.PROC=PROC
        self.procmod = __import__('pyastra.ports.pic14.procs.%s' %PROC, globals(), locals(), '*')
        self.hdikt = self.procmod.hdikt
        self.pages = self.procmod.pages
        self.shareb = self.procmod.shareb
        self.vectors = self.procmod.vectors
        self.maxram = self.procmod.maxram
        self.say = say
        
        self.max_ram=0
        for i in self.procmod.banks:
            self.max_ram += i[1] - i[0] + 1
        
        self.max_instr=0
        for i in self.pages:
            self.max_instr += i[1] - i[0] + 1
    
    def convert(self, node):
        proc_clean=self.PROC
        if proc_clean[-1]=='i':
            proc_clean = proc_clean[:-1]
        self.head="""
\tprocessor\t%s
\t#include\tp%s.inc

""" % (proc_clean, proc_clean)
        if self.pages[0][0]>0:
            self.instr = 1
        else:
            self.instr = 0

        self.cvar=mem(self.procmod.banks)
        if self.ICD:
            self.instr += 1
            
        self._convert(ImportFrom('builtins', [('*', None)]))
        self.asm=0
        
        addrs=[]
        if node.interrupts_on:
            for part in self.shareb:
                #Check that part is not SFR
                addrs=[]
                in_bank = 0
                for bank in self.procmod.banks:
                    if bank[0] <= part[0][0] <= bank[1]:
                        in_bank = 1
                        break
                    
                if not in_bank or part[0][1]-part[0][0]+1 < 4:
                    continue

                in_banks_until = -1
                
                for sub in part:
                    if sub[0] >> 7 == in_banks_until + 1:
                        in_banks_until += 1
                    else:
                        break
                
                if in_banks_until == self.maxram >> 7:
                    for i in xrange(part[0][0], part[0][1]+1):
                        if not self.cvar.is_reserved(i):
                            addrs += [i]
                            if len(addrs) == 5:
                                break
                    if len(addrs) == 5:
                        break
        if len(addrs)==5:
            self.malloc('var_w_temp', addr=addrs[0])
            self.malloc('var_status_temp', addr=addrs[1])
            self.malloc('var_pclath_temp', addr=addrs[2])
            self.malloc('var_test_temp', addr=addrs[3])
            self.malloc('var_test', addr=addrs[4])
        else:
            self.malloc('var_test')
        
        self._convert(node)
        
        body_buf = ["""
\terrorlevel\t-302
\terrorlevel\t-306
"""]

        if self.vectors:
            body_buf += ['\n\torg\t%s\n' % hex(self.vectors[0])]
        else:
            body_buf += ['\n\torg\t0x0\n']
        
        if self.ICD:
            body_buf += ['\tnop\n']

        if self.pages[0][0]>0:
            body_buf += ["""
\tgoto\tmain\n"""]
            if self.interr_instr:
                if len(self.pages) > 1:
                    self.interr += """
        movf    var_test_temp,      W
        movwf   var_test
        movf    var_pclath_temp,    W
        movwf   PCLATH
        swapf   var_status_temp,    W
        movwf   STATUS
        swapf   var_w_temp, F
        swapf   var_w_temp, W
        retfie\n"""
                    self.interr_instr += 9
                else:
                    self.interr += """
        movf    var_test_temp,      W
        movwf   var_test
        swapf   var_status_temp,    W
        movwf   STATUS
        swapf   var_w_temp, F
        swapf   var_w_temp, W
        retfie\n"""
                    self.interr_instr += 7
                self.instr += self.interr_instr
                body_buf += ["\n\torg\t%s\n" % hex(self.vectors[1]), self.interr]
            if self.pages[0][0] > self.vectors[1]+self.interr_instr:
                body_buf += ["\n\torg\t%s" % hex(self.pages[0][0])]
            body_buf += ["\nmain\n"]

        self.body = body_buf + self.body
        
        if self.ICD:
            self.ram_usage += 1

        self.body += ['\n\tgoto\t$\n']
        self.instr += 1
            
        ftest=0
        self.tail=fbuf=''
        t_instr = self.pages[0][0]+self.instr
        for i in self.funcs:
            if not self.funcs[i][1]:
                self.say('Undefined function call: %s' % i)
            if self.funcs[i][3]:
                ftest=1
                (t_str, t_instr) = self.page_org(t_instr, self.funcs[i][2])
                fbuf += t_str
                fbuf += self.funcs[i][1]
                self.instr += self.funcs[i][2]
                
        if ftest:
            self.tail += "\n;\n; SUBROUTINES\n;\n\n%s" % fbuf
            
        self.tail += "\n\tend\n"
        self.instr=t_instr
        
    def _convert(self, node):
        if node==None:
            return
        elif isinstance(node, list):
            for n in node:
                self._convert(n)
        elif isinstance(node, Add):
            self._convert(node.left)
            buf=self.push()
            self.app('movwf', buf)
            self._convert(node.right)
            self.app('addwf', buf, 'w')
            self.pop()
        elif isinstance(node, And):
            end_lbl=self.getLabel()
            for n in xrange(len(node.nodes)):
                self._convert(node.nodes[n])
                if n+1 != len(node.nodes):
                    self.del_last=0
                    self.app('btfsc', 'STATUS', 'Z')
                    self.app('goto', end_lbl)
            self.del_last=0
            self.app(end_lbl, verbatim=1)
#       elif isinstance(node, AssAttr):
#       elif isinstance(node, AssList):
        elif isinstance(node, Name):
            if node.flags=='OP_ASSIGN':
                if node.name in self.hdikt:
                    name=node.name
                else:
                    name='_'+node.name
                    self.malloc(name)
                self.app('movwf', name)
#            elif node.flags=='OP_DELETE':
#                self.free('_'+node.name)
            else:
                self.say('%s flag is not supported while.' % node.flags, self.lineno(node))
#       elif isinstance(node, AssTuple):
#       elif isinstance(node, Assert):
        elif isinstance(node, Assign):
            all_names=1
            any_sscr=0
            all_sscr=1
            for n in node.nodes:
                if not isinstance(n, AssName):
                    all_names=0
                if isinstance(n, Subscript):
                    any_sscr=1
                else:
                    all_sscr=0
                    
            if all_names and isinstance(node.expr, Const) and node.expr.value == 0:
                for n in node.nodes:
                    if n.name in self.hdikt:
                        name=n.name
                    else:
                        name='_'+n.name
                        self.malloc(name)
                    self.app('clrf', name)
            elif any_sscr:
                if not all_sscr:
                    self.say('mixing bit and byte assign is not supported.', self.lineno(node))
                elif isinstance(node.expr, Const):
                    if node.expr.value:
                        oper='bsf'
                    else:
                        oper='bcf'
                        
                    for n in node.nodes:
                        if not isinstance(n.expr, Name):
                            self.say('Bit assign may be applied to bytes only.', self.lineno(node))
                        else:
                            name=n.expr.name
                            if name not in self.hdikt:
                                name='_'+name
                                self.malloc(name)
                            for i in n.subs:
                                if isinstance(i, Const):
                                    self.app(oper, name, str(i.value))
                                elif isinstance(i, Name) and i.name in self.hdikt:
                                        self.app(oper, name, str(i.name))
                                elif oper=='bsf':
                                    self._convert(AugAssign(n.expr, '|=', LeftShift((Const(1), i))))
                                else:
                                    self._convert(AugAssign(n.expr, '&=', Invert(LeftShift((Const(1), i)))))
##                                        self._convert(If([(Subscript(Name('c'), 'OP_APPLY', [Name('d')]), Stmt([AugAssign(Name('a'), '|=', LeftShift((Const(1), Name('b')))), AugAssign(Name('a'), '&=', Invert(LeftShift((Const(1), Name('b')))))]))], None))
                elif isinstance(node.expr, Subscript) and len(node.expr.subs) == 1 and isinstance(node.expr.subs[0], Const):
                    lbl_else=self.getLabel()
                    lbl_exit=self.getLabel()

                    ename=node.expr.expr.name
                    if ename not in self.hdikt:
                        ename='_'+ename
                        self.malloc(ename)
                    self.app('btfsc', ename, str(node.expr.subs[0].value))
                    self.app('goto', lbl_else)
                    for n in node.nodes:
                        if not isinstance(n.expr, Name):
                            self.say('Bit assign may be applied to bytes only.', self.lineno(node))
                        else:
                            name=n.expr.name
                            if name not in self.hdikt:
                                name='_'+name
                                self.malloc(name)
                            for i in n.subs:
                                if isinstance(i, Const):
                                    self.app('bcf', name, str(i.value))
                                elif isinstance(i, Name) and i.name in self.hdikt:
                                    self.app('bcf', name, str(i.name))
                                else:
                                    self.say('Only constant indices are supported while.', self.lineno(node))
                    self.app('goto', lbl_exit)
                    self.app('\n%s' % lbl_else, verbatim=1)
                    for n in node.nodes:
                        if not isinstance(n.expr, Name):
                            self.say('Bit assign may be applied to bytes only.', self.lineno(node))
                        else:
                            name=n.expr.name
                            if name not in self.hdikt:
                                name='_'+name
                                self.malloc(name)
                            for i in n.subs:
                                if isinstance(i, Const):
                                    self.app('bsf', name, str(i.value))
                                elif isinstance(i, Name) and i.name in self.hdikt:
                                    self.app('bsf', name, str(i.name))
                                else:
                                    self.say('Only constant indices are supported while.', self.lineno(node))
                    self.app('\n%s' % lbl_exit, verbatim=1)
                else:
                    self._convert(If([(node.expr,
                        Stmt([Assign(node.nodes, Const(1))]))],
                        Stmt([Assign(node.nodes, Const(0))])))
            else:
                self._convert(node.expr)
                
                for n in node.nodes:
                    self._convert(n)
        elif isinstance(node, AugAssign):
                if not isinstance(node.node, Name):
                    self.say('assign only to a variable is not supported while.', self.lineno(node))

                name=node.node.name
                if '_'+name in self.dikt:
                    name = '_'+name
                elif name not in self.hdikt:
                    self.say('variable %s not initialized' % name, self.lineno(node))
                    
                if node.op == '+=':
                    self._convert(node.expr)
                    self.app('addwf', name, 'f')
                elif node.op == '-=':
                    self._convert(node.expr)
                    self.app('subwf', name, 'f')
                elif node.op == '*=':
                    self._convert(Mul((node.node, node.expr)))
                    self.app('movwf', name, 'f')
                elif node.op == '/=':
                    self._convert(Div((node.node, node.expr)))
                    self.app('movwf', name, 'f')
                elif node.op == '%=':
                    self._convert(Mod((node.node, node.expr)))
                    self.app('movwf', name, 'f')
                elif node.op == '**=':
                    self._convert(Power((node.node, node.expr)))
                    self.app('movwf', name, 'f')
                elif node.op == '>>=':
                    self._convert(RightShift((node.node, node.expr)))
                    self.app('movwf', name, 'f')
                elif node.op == '<<=':
                    self._convert(LeftShift((node.node, node.expr)))
                    self.app('movwf', name, 'f')
                elif node.op == '&=':
                    self._convert(node.expr)
                    self.app('andwf', name, 'f')
                elif node.op == '^=':
                    self._convert(node.expr)
                    self.app('xorwf', name, 'f')
                elif node.op == '|=':
                    self._convert(node.expr)
                    self.app('iorwf', name, 'f')
                else:
                    self.say('augmented assign %s is not supported while.' % node.op, self.lineno(node))
                    
#      elif isinstance(node, Backquote):
        elif isinstance(node, BitAnd):
            buf=self.push()
            self._convert(node.nodes[0])
            self.app('movwf', buf)
            for n in node.nodes[1:-1]:
                self._convert(n)
                self.app('andwf', buf, 'f')
            self._convert(node.nodes[-1])
            self.app('andwf', buf, 'w')
            self.pop()
        elif isinstance(node, BitOr):
            buf=self.push()
            self._convert(node.nodes[0])
            self.app('movwf', buf)
            for n in node.nodes[1:-1]:
                self._convert(n)
                self.app('iorwf', buf, 'f')
            self._convert(node.nodes[-1])
            self.app('iorwf', buf, 'w')
            self.pop()
        elif isinstance(node, BitXor):
            buf=self.push()
            self._convert(node.nodes[0])
            self.app('movwf', buf)
            for n in node.nodes[1:-1]:
                self._convert(n)
                self.app('xorwf', buf, 'f')
            self._convert(node.nodes[-1])
            self.app('xorwf', buf, 'w')
            self.pop()
        elif isinstance(node, Break):
            self.app('goto', self.lbl_stack[-1][1])
        elif isinstance(node, Call):
            if getattr(node, 'starreds', None) or getattr(node, 'keywords', None):
                self.say('*-args and **-args are not supported while')
                
            if not isinstance(node.func, Name):
                self.say('only functions are callable while')

            if node.func.id == 'asm':
                err_mesg='asm function has the following syntax: asm(code [, instr_count [, (local_var1, local_var2, ...)]])'
                if len(node.args) == 1 and isinstance(node.args[0], Constant):
                    self.app('\n; -- Parsed verbatim inclusion:\n', verbatim=1)
                    prev_op=''
                    for s in node.args[0].value.splitlines(1):
                        #FIXME: bad tokenizing in case of "' '" or "','" as constants
                        op=[]
                        for op0 in s.split():
                            for op1 in op0.split(','):
                                if op1:
                                    op += [op1]
                        comment=''
                        for wn in range(len(op)):
                            if op[wn][0]==';':
                                comment=s[s.find(op[wn]):]
                                op=op[:wn]
                                break
                        if not op:
                            self.app(comment, verbatim=1)
                        elif len(op) > 3 or ((op[0] not in self.bank_cmds) and (op[0] not in self.no_bank_cmds)):
                            if s[0].isspace():
                                self.say('Can\'t parse line in asm function:\n%s' % s, level=self.warning)
                                self.asm=1
                                self.last_bank = self.prelast_bank = self.curr_bank=-1

                            self.app(s, verbatim=1)
                        else:
                            op[0]=op[0].lower()
                            if len(op) == 3:
                                op[1]=op[1]
                                
                            if len(op) > 1 and (op[0] in self.bank_cmds or op[0] in self.no_bank_cmds) and op[0][-1] in 'fzcs':
                                if op[1] not in self.hdikt and op[1] not in self.dikt:
                                    op[1]=op[1]
                                    self.malloc(op[1])

                            comment=comment[1:]
                            t_instr=self.instr
                            if len(op)==1:
                                self.app(op[0], comment=comment)
                            elif len(op)==2:
                                self.app(op[0], op[1], comment=comment)
                            else:
                                self.app(op[0], op[1], op[2], comment=comment)

                            if self.instr - t_instr > 1 and prev_op in self.cond_br_cmds:
                                last=self.body[-1]
                                del self.body[-1]
                                lbl_exit=self.getLabel()

                                if prev_op=='btfsc':
                                    s=self.body[-1]
                                    self.body[-1]=s[:s.find(prev_op)]+'btfss'+s[s.find(prev_op)+5:]
                                    self.app('goto', lbl_exit)
                                elif prev_op=='btfss':
                                    s=self.body[-1]
                                    self.body[-1]=s[:s.find(prev_op)]+'btfsc'+s[s.find(prev_op)+5:]
                                    self.app('goto', lbl_exit)
                                else:
                                    lbl_if=self.getLabel()
                                    self.app('goto', lbl_if)
                                    self.app('goto', lbl_exit)
                                    
                                    self.app(lbl_if, verbatim=1)

                                self.body += [last]
                                self.app(lbl_exit, verbatim=1)
                                
                        if op:
                            prev_op=op[0]
                    self.app('\n; -- End of parsed verbatim inclusion\n', verbatim=1)
                elif not (2 <= len(node.args) <= 3 and isinstance(node.args[0], Const) and isinstance(node.args[1], Const)):
                    self.say(err_mesg, exit_status=2)
                else:
                    self.app('\n\terrorlevel\t+302\n', verbatim=1)
                    if len(node.args) > 2:
                        if not isinstance(node.args[2], Tuple):
                            self.say(err_mesg, exit_status=2)
                        else:
                            for i in node.args[2].nodes:
                                if not isinstance(i, Const):
                                    self.say('Local variables names must be constant strings.', exit_status=2)
                                self.malloc(i.value, 1)
                    
                    self.app('\n; -- Verbatim inclusion:\n%s\n; -- End of verbatim inclusion\n' % node.args[0].value, verbatim=1)
                    self.instr += node.args[1].value
                    self.asm=1
                    self.last_bank = self.prelast_bank = self.curr_bank = -1
                    self.app('\n\terrorlevel\t-302\n', verbatim=1)
            elif node.node.name == 'halt':
                if len(node.args) != 0:
                    self.say('halt() function takes no arguments', exit_status=2)
                self.app('goto', '$')
            elif node.node.name == 'sleep':
                if len(node.args) != 0:
                    self.say('sleep() function takes no arguments', exit_status=2)
                self.app('sleep')
                self.app('nop')
            elif node.node.name == 'fbin':
                if len(node.args) != 1 or not isinstance(node.args[0], Const) or not isinstance(node.args[0].value, str):
                    self.say('fbin(\'0101 0101\') function takes only one argument: binary number', exit_status=2)
                
                val=0
                for i in node.args[0].value:
                    if i != ' ':
                        val=val << 1
                        if i == '1':
                            val+=int(i)
                        elif i != '0':
                            self.say('fbin(\'0101 0101\') function takes only one argument: binary number', exit_status=2)
                    
                self._convert(Const(val))
            else:
                if node.node.name not in self.funcs:
                    self.say('function %s is not defined before call (this is not supported while)' % node.node.name, self.lineno(node), exit_status=1)
                    args=[]
                    self.funcs[node.node.name]=[node.args, None, None, 1, '']
                else:
                    self.funcs[node.node.name][3]=1
                    
                if  len(self.funcs[node.node.name][0]) != len(node.args):
                    self.say('function %s takes exactly %g argument(s)' % (node.node.name, len(self.funcs[node.node.name][0])), exit_status=2)
                             
                for i in xrange(len(node.args)):
                    (aname, val)=(self.funcs[node.node.name][0][i], node.args[i])
                    self._convert(val)
                    self.app('movwf', '_'+aname)
                self.app('call', 'func_%s' % node.node.name)
                    
##      elif isinstance(node, Class):
        elif isinstance(node, Compare):
            if len(node.ops) != 1:
                self.say('Currently multiple comparisions are not supported', self.lineno(node))
            buf = self.push()
            nodes=node.ops
            if nodes[0][0]=='<':
                lbl_false=self.getLabel()
                self._convert(node.expr)
                self.app('movwf', buf)
                self._convert(nodes[0][1])
                self.app('subwf', buf, 'w') # node.expr - nodes[0][1] should be < 0 (Z=0 and C=0)
                self.app('btfsc', 'STATUS', 'Z')
                self.app('goto', lbl_false) # node.expr = nodes[0][1]
                self.app('bcf', 'STATUS', 'Z') # true
                self.app('btfsc', 'STATUS', 'C')
                self.app(lbl_false, verbatim=1)
                self.app('bsf', 'STATUS', 'Z') # false
            elif nodes[0][0]=='>':
                lbl_false=self.getLabel()
                self._convert(node.expr)
                self.app('movwf', buf)
                self._convert(nodes[0][1])
                self.app('subwf', buf, 'w') # node.expr - nodes[0][1] should be > 0 (Z=0 and C=1)
                self.app('btfsc', 'STATUS', 'Z')
                self.app('goto', lbl_false) # node.expr = nodes[0][1]
                self.app('bcf', 'STATUS', 'Z') # true
                self.app('btfss', 'STATUS', 'C')
                self.app(lbl_false, verbatim=1)
                self.app('bsf', 'STATUS', 'Z') # false
            elif nodes[0][0]=='==':
                self._convert(node.expr)
                self.app('movwf', buf)
                self._convert(nodes[0][1])
                self.app('subwf', buf, 'w')
                self.app('movf', 'STATUS', 'w')
                self.app('xorlw', '1 << Z')
                self.app('movwf', 'STATUS')
            elif nodes[0][0]=='<=':
                lbl_true=self.getLabel()
                self._convert(node.expr)
                self.app('movwf', buf)
                self._convert(nodes[0][1])
                self.app('subwf', buf, 'w') # node.expr - nodes[0][1] should be <= 0 (Z=1 or C=0)
                self.app('btfsc', 'STATUS', 'Z')
                self.app('goto', lbl_true) # node.expr = nodes[0][1]
                self.app('bsf', 'STATUS', 'Z') # false
                self.app('btfss', 'STATUS', 'C')
                self.app(lbl_true, verbatim=1)
                self.app('bcf', 'STATUS', 'Z') # true
            elif nodes[0][0]=='>=':
                lbl_true=self.getLabel()
                self._convert(node.expr)
                self.app('movwf', buf)
                self._convert(nodes[0][1])
                self.app('subwf', buf, 'w') # node.expr - nodes[0][1] should be >= 0 (Z=1 or C=1)
                self.app('btfsc', 'STATUS', 'Z')
                self.app('goto', lbl_true) # node.expr = nodes[0][1]
                self.app('bsf', 'STATUS', 'Z') # false
                self.app('btfsc', 'STATUS', 'C')
                self.app(lbl_true, verbatim=1)
                self.app('bcf', 'STATUS', 'Z') # true
            elif nodes[0][0]=='!=':
                self._convert(node.expr)
                self.app('movwf', buf)
                self._convert(nodes[0][1])
                self.app('subwf', buf, 'w')
##            elif nodes[0][0]=='is':
##            elif nodes[0][0]=='is not':
##            elif nodes[0][0]=='in':
##            elif nodes[0][0]=='not in':
            else:
                self.say('comparision %s is not supported while.' % node.op, self.lineno(node))
                    
            self.pop()
        elif isinstance(node, Constant):
            self.app('movlw', self.formatConst(node.value))
            self.test()
        elif isinstance(node, Continue):
            self.app('goto', self.lbl_stack[-1][0])
##      elif isinstance(node, Dict):
        elif isinstance(node, Expr):
            if isinstance(node.value, Constant) and node.value.value==None:
                return
            else:
                self._convert(node.value)
        elif isinstance(node, Div):
            self._convert(Expr(Call(Name('div'), [node.left, node.right], None, None)))
##      elif isinstance(node, Ellipsis):
##      elif isinstance(node, Exec):
        elif isinstance(node, For):
            if not (isinstance(node.list, Call) and
                    isinstance(node.list.node, Name) and
                    node.list.node.name=='xrange' and
                    len(node.list.args)==2 and
                    node.list.star_args==None and
                    node.list.dstar_args==None):
                self.say('only "for <var> in xrange(<from>, <to>)" for statement is supported while', self.lineno(node))
                return
            cntr = node.assign.name
            if cntr not in self.hdikt:
                cntr = '_'+cntr
            self._convert(Assign([node.assign], node.list.args[0]))
            
            lbl_beg=self.getLabel()
            lbl_else=self.getLabel()
            lbl_cont=self.getLabel()
            if node.else_ != None:
                lbl_end=self.getLabel()
            else:
                lbl_end=lbl_else

            self.lbl_stack += (lbl_cont, lbl_end)
                
            if isinstance(node.list.args[1], Constant) and node.list.args[1].value==256:
                #skip whole loop if cntr==255
                self.app('movf', cntr, 'w')
                self.app('sublw', '0xff')
                self.app('btfsc', 'STATUS', 'Z')
                self.app('goto', lbl_else)
                
                self.app('\n%s' % lbl_beg, verbatim=1)
                
                self._convert(node.body)
                
                self.app('\n%s' % lbl_cont, verbatim=1)
                
                self.app('incf', cntr, 'f')

                self.app('movf', cntr, 'f')
                self.app('btfss', 'STATUS', 'Z')
                self.app('goto', lbl_beg)
            else:
                limit = self.push()
                self._convert(node.list.args[1])
                self.app('movwf', limit)
                
                self.app('\n%s' % lbl_beg, verbatim=1)
                
                self.app('movf', limit, 'w')
                self.app('subwf', cntr, 'w')
                self.app('btfsc', 'STATUS', 'Z') #skip if cntr - limit != 0
                self.app('goto', lbl_else)
                self.app('btfsc', 'STATUS', 'C') #skip if cntr - limit  < 0
                self.app('goto', lbl_else)
                
                self._convert(node.body)
                
                self.app('\n%s' % lbl_cont, verbatim=1)
                
                self.app('incf', cntr, 'f')
                self.app('goto', lbl_beg)
            
            if node.else_ != None:
                self.app('\n%s' % lbl_else, verbatim=1)
                self._convert(node.else_)
            
            self.app('\n%s' % lbl_end, verbatim=1)
            self.pop()
            del self.lbl_stack[-1]
        elif isinstance(node, ImportFrom):
            if node.names != [('*', None)]:
                self.say('only "from <module_name> import *" input statement is supported while', self.lineno(node))
                return
            name='%s.py' % node.module
            if not os.path.exists(name):
                name=os.path.join(pyastra.ports.pic14.__path__[0], name)
            root=parse(open(name).read(),filename=name)
            self._convert(root)
        elif isinstance(node, FunctionDef):
            used=0
            if (node.name in self.funcs):
                if self.funcs[node.name][1]:
                    self.say('function %s is already defined.' % node.name, exit_status=2)
                else:
                    if len(self.funcs[node.name][0])==len(node.args.args): 
                        self.say('function %s takes exactly %g arguments' % (node.name, len(self.funcs[node.name][0])), exit_status=2)
                    used=1
                        
            
            
            if node.args.defaults:
                self.say('function defaults are not supported while.')
                        
            for a in node.args.args:  
                self.malloc('_'+a.arg, 1)  

                
            tbody=self.body
            tinstr=self.instr
            tcurr_bank=self.curr_bank
            tlast_bank=self.last_bank
            tprelast_bank=self.prelast_bank
            
            self.infunc = 1
            self.curr_bank = -1
            self.last_bank = -1
            self.prelast_bank = -1
            if node.name == 'on_interrupt':
                self.in_inter=1
                if not self.vectors:
                    self.say('Selected processor does not support interrupts!', level=self.error, exit_status=1)
                if not self.dikt.has_key('var_w_temp'):
                    self.say('Pyastra doesn\'t suppoort interrupts for selected processor while.', level=self.error, exit_status=1)
                self.inter_ret=self.getLabel()
                if self.interr:
                    self.say('One or more interrupt handlers already defined. New one is appendet to previous.', level=self.message)
                    self.body = []
                else:
                    if len(self.pages) > 1:
                        self.body = ["""
        movwf   var_w_temp
        swapf   STATUS, W
        movwf   var_status_temp
        movf    PCLATH, W
        movwf   var_pclath_temp
        movf    var_test, W
        movwf   var_test_temp
        bcf     PCLATH, 3
        bcf     PCLATH, 4
        """]
                        self.instr = 9
                    else:
                        self.body = ["""
        movwf   var_w_temp
        swapf   STATUS, W
        movwf   var_status_temp
        movf    var_test, W
        movwf   var_test_temp
        """]
                        self.instr = 5
                self.body += ['\n;\n; * Interrupts handler *\n;\n']
            else:
                self.body=['\n;\n; * Function %s *\n;\n' % node.name]
                self.app('func_%s\n' % node.name, verbatim=1)
                self.instr=0
            self._convert(node.body)
            
            if not (hasattr(node.body, 'nodes') and isinstance(node.body.nodes[-1], Return) or hasattr(node.body, 'body') and isinstance(node.body.body[-1], Return)) and node.name != 'on_interrupt':
                self.app('return')
                
            self.prelast_bank = -1
            if node.name == 'on_interrupt':
                self.app(self.inter_ret, verbatim=1)
                self.app(';\n; * End of interrups handler *\n;', verbatim=1)
                body_joined=''.join(self.body)
                self.interr += body_joined
                self.interr_instr += self.instr
            else:
                self.app(';\n; * End of function %s *\n;' % node.name, verbatim=1)
                body_joined=''.join(self.body)
                self.funcs[node.name]=[node.args, body_joined, self.instr, used, self.head]
            self.infunc=self.in_inter=0
            self.instr=tinstr
            self.curr_bank=tcurr_bank
            self.last_bank=tlast_bank
            self.prelast_bank=tprelast_bank
            self.body=tbody
#       elif isinstance(node, Getattr):
#       elif isinstance(node, Global):
        elif isinstance(node, If):
            self.app(verbatim=1)
            exit_lbl=self.getLabel()
            
            for n in node.tests:
                self._convert(n[0])
                self.del_last=0
                label=self.getLabel()
                self.app('btfsc', 'STATUS', 'Z')
                self.app('goto', label)
                self._convert(n[1])
                self.app('goto', exit_lbl)
                self.app('%s' % label, verbatim=1)
            self._convert(node.else_)
            self.app('%s' % exit_lbl, verbatim=1)
#       elif isinstance(node, Import):
        elif isinstance(node, Invert):
            self._convert(node.expr)
            buf=self.push()
            self.app('movwf', buf)
            self.app('comf', buf, 'w')
            self.pop()
#       elif isinstance(node, Keyword):
#       elif isinstance(node, Lambda):
        elif isinstance(node, LShift):
            if isinstance(node.right, Const) and self.formatConst(node.right.value)!=-1 and (node.right.value < 8 or self.op_speed):
                buf=self.push()
                self._convert(node.left)
                self.app('movwf', buf)
                for i in xrange(node.right.value-1):
                    self.app('rlf', buf, 'f')
                self.app('rlf', buf, 'w')
                self.pop()
            else:
                self._convert(Discard(CallFunc(Name('lshift'), [node.left, node.right], None, None)))
                
#       elif isinstance(node, List):
#       elif isinstance(node, ListComp):
#       elif isinstance(node, ListCompFor):
#       elif isinstance(node, ListCompIf):
        elif isinstance(node, Mod):
            self._convert(Discard(CallFunc(Name('mod'), [node.left, node.right], None, None)))
        elif isinstance(node, Module):
            if hasattr(node, 'body'):  # Для Python 3.8+
                self._convert(node.body)
            elif hasattr(node, 'node'):  # Для старых версий Python
                self._convert(node.node)
            else:
                self.say('Unsupported Module node structure', level=self.error)
        elif isinstance(node, Mult):
            self._convert(Discard(CallFunc(Name('mul'), [node.left, node.right], None, None)))
        elif isinstance(node, Name):
            if '_'+node.name in self.dikt:
                self.app('movf', '_'+node.name, 'w')
            elif node.name in self.hdikt:
                self.app('movf', node.name, 'w')
            else:
                self.say('variable %s not initialized' % node.name, self.lineno(node))
        elif isinstance(node, Not):
            lbl1=self.getLabel()
            lbl_end=self.getLabel()
            self._convert(node.expr)
            self.del_last=0
            self.app('btfsc', 'STATUS', 'Z')
            self.app('goto', lbl1)
            self.app('movlw', '0')
            self.app('goto', lbl_end)
            self.app(lbl1, verbatim=1)
            self.app('movlw', '1')
            self.app(lbl_end, verbatim=1)
            self.test()
        elif isinstance(node, Or):
            lbl_end=self.getLabel()
            for n in xrange(len(node.nodes)):
                self._convert(node.nodes[n])
                self.del_last=0
                if n+1 != len(node.nodes):
                    self.app('btfss', 'STATUS', 'Z')
                    self.app('goto', lbl_end)
            self.app(lbl_end, verbatim=1)
        elif isinstance(node, Pass):
            #self.app('nop')
            pass
        elif isinstance(node, BinOp) and isinstance(node.op, Pow):
            self._convert(Discard(CallFunc(Name('mul'), [node.left, node.right], None, None)))
#       elif isinstance(node, Print):
#       elif isinstance(node, Printnl):
#       elif isinstance(node, Raise):
        elif isinstance(node, Return):
            if not (isinstance(node.value, Const) and node.value.value==None):
                if self.in_inter:
                    self.say('Interrupt handler can not return any values! Ignoring...', level=self.warning)
                else:
                    self._convert(node.value)
                    self.del_last = 0
            
            if self.in_inter:
                self.app('goto', self.inter_ret)
            else:
                self.app('return')
        elif isinstance(node, RShift):
            if isinstance(node.right, Const) and self.formatConst(node.right.value)!=-1 and (node.right.value < 8 or self.op_speed):
                buf=self.push()
                self._convert(node.left)
                self.app('movwf', buf)
                for i in xrange(node.right.value-1):
                    self.app('rrf', buf, 'w')
                    
                self.app('rrf', buf, 'f')
                self.pop()
            else:
                self._convert(Discard(CallFunc(Name('rshift'), [node.left, node.right], None, None)))
#       elif isinstance(node, Slice):
#       elif isinstance(node, Sliceobj):
        elif isinstance(node, stmt):
            self._convert(node.nodes)
        elif isinstance(node, Sub):
            self._convert(node.left)
            buf=self.push()
            self.app('movwf', buf)
            self._convert(node.right)
            self.app('subwf', buf, 'w')
            self.pop()
        elif isinstance(node, Subscript):
            if not isinstance(node.expr, Name):
                self.say('Bit assign may be applied to bytes only.', self.lineno(node))
            elif len(node.subs) != 1:
                self.say('More than one subscripts are not fully supported while.', self.lineno(node))
            elif not node.flags=='OP_APPLY':
                self.say('Unsupported flag: %s.' % node.flags, self.lineno(node))
            else:
                name=node.expr.name
                if name in self.hdikt:
                    pass
                else:
                    name='_'+name
                    self.malloc(name)
                if isinstance(node.subs[0], Const):
                    self.app('movlw', '.0')
                    self.app('btfsc', name, str(node.subs[0].value))
                    self.app('movlw', '.1')
                elif isinstance(node.subs[0], Name):
                    if node.subs[0].name in self.hdikt:
                        self.app('movlw', '.0')
                        self.app('btfsc', name, node.subs[0].name)
                        self.app('movlw', '.1')
                    else:
                        self._convert(Bitand([node.expr, LeftShift((Const(1), node.subs[0]))]))
                else:
                    self.say('Only constant indices are supported while.', self.lineno(node))
                self.test()
#       elif isinstance(node, TryExcept):
#       elif isinstance(node, TryFinally):
#       elif isinstance(node, Tuple):
        elif isinstance(node, UnaryOp):
            self._convert(node.expr)
##        elif isinstance(node, Attribute):
##            self.say('Attribute access is not supported: %s' % node.attr, self.lineno(node))
#       elif isinstance(node, UnarySub):
        elif isinstance(node, While):
            lbl_beg=self.getLabel()
            lbl_else=self.getLabel()
            if node.else_ != None:
                lbl_end=self.getLabel()
            else:
                lbl_end=lbl_else
            self.lbl_stack.append((lbl_beg, lbl_end))
            self.app('\n%s' % lbl_beg, verbatim=1)
            self._convert(node.test)
            self.del_last=0
            self.app('btfsc', 'STATUS', 'Z')
            self.app('goto', '%s\n' % lbl_else)
            self._convert(node.body)
            self.app('goto', lbl_beg)
            if node.else_ != None:
                self.app('\n%s' % lbl_else, verbatim=1)
                self._convert(node.else_)
            self.app('\n%s' % lbl_end, verbatim=1)
            del self.lbl_stack[-1]
#       elif isinstance(node, Yield):
        else:
            self.say('"%s" node is not supported while.' % node.__class__.__name__, self.lineno(node))
            
    def formatConst(self, c):
        if type(c) == types.IntType and 0 <= int(c) <= 0xff:
            return hex(c)
        elif type(c) == types.StringType and len(c)==1:
            return "'%s'" % c
        else:
            self.say('%s type constant is not supported while.' % c.__class__.__name__)
            return c

    def lineno(self, node):
        if hasattr(node, 'lineno'):
            return node.lineno
        else:
            return None
            
    def push(self):
        self.stack += 1
        name='stack%g' % self.stack
        self.malloc(name)
        return name
        
    def pop(self):
        pass # this feature is temporary off due to bugs it causes in some cases
        #self.stack -= 1
        #self.free('stack%g' % self.stack)
        
    def getLabel(self):
        self.label += 1
        return 'label%i' % self.label
    
    def malloc(self, name, care=0, addr=None):
        if name not in self.dikt:
            if addr == None:
                try:
                    addr=self.cvar.reserve_byte()
                except:
                    self.say("program does not fit RAM.", level=self.error)
                    return
            else:
                try:
                    self.cvar.reserve_byte(addr)
                except:
                    self.say("address %i is not allocatable" % addr, level=self.warning)
                    return
            
            self.dikt[name]=addr
            if len(self.dikt) > self.ram_usage:
                self.ram_usage=len(self.dikt)
                
            self.head += '%s\tequ\t%s\t;bank %g\n' % (name, hex(addr), addr >> 7)
        elif care:
            self.say("name %s is defined twice!" % name, level=self.warning)

#    def free(self, name, care=1):
#        if name in self.dikt:
#            self.cvar.insert(0, self.dikt[name])
#            del self.dikt[name]
#        elif care:
#            self.say("variable %s can't be deleted before assign!" % name, level=self.warning)

    def bank_by_name(self, name):
        if name in self.dikt:
            addr = self.dikt[name]
        elif name in self.hdikt:
            if name in self.bank_indep:
                return ''
            addr = self.hdikt[name]
        else:
            return ''

        bank = addr >> 7
        addr7 = addr & 0x7f

        if self.maxram < 0x80 or (not 'RP0' in self.hdikt):
            return ''
        
        ret=''
        if self.curr_bank != -1:
            for block in self.shareb:
                addr_in_block = 0
                curr_block_has = 0
            
                for sub in block:
                    if sub[0] <= addr <= sub[1]:
                        addr_in_block = 1
                    
                    if sub[0] <= (addr7 | (sub[0] >> 7 << 7)) <= sub[1]:
                        curr_block_has = 1
                
                if addr_in_block and curr_block_has:
                    self.prelast_bank=self.last_bank
                    self.last_bank=self.curr_bank
                    return ''
        else:
            for block in self.shareb:
                addr_in_block = 0
                curr_block_has = 1
            
                for sub in block:
                    if sub[0] <= addr7 <= sub[1]:
                        addr_in_block = 1
                    
                    if  not (sub[0] <= (addr7 | (sub[0] >> 7 << 7)) <= sub[1]):
                        curr_block_has = 0
                
                if addr_in_block:
                    if curr_block_has:
                        self.prelast_bank=self.last_bank
                        self.last_bank=self.curr_bank
                        return ''
                    else:
                        break
            
        if self.curr_bank==-1 or ((bank & 1) ^ (self.curr_bank & 1)):
            if bank & 1:
                ret += '\tbsf\tSTATUS,\tRP0\n'
            else:
                ret += '\tbcf\tSTATUS,\tRP0\n'
            self.instr += 1
           
        if self.curr_bank==-1 or (((bank & 2) ^ (self.curr_bank & 2))) and self.maxram > 0xff and 'RP1' in self.hdikt:
            if bank & 2:
                ret += '\tbsf\tSTATUS,\tRP1\n'
            else:
                ret += '\tbcf\tSTATUS,\tRP1\n'
            self.instr += 1
            
        self.prelast_bank=self.last_bank
        self.last_bank=self.curr_bank
        self.curr_bank=bank
        return ret

    def page_org(self, instr, f_instr):
        if self.pages[self.cur_page][1] >= instr + f_instr:
            return ('', instr+f_instr)
        else:
            self.cur_page += 1
            if len(self.pages)==self.cur_page:
                self.say('Program doesn\'t fit program memory.', level=self.error, exit_status=1)
            return ('\torg\t%s\n' % hex(self.pages[self.cur_page][0]), self.pages[self.cur_page][0]+f_instr)
    
    def test(self):
        self.app('movwf', 'var_test')
        self.app('movf', 'var_test', 'f')
        self.del_last=1

    #ve=0
    def app(self, cmd='', op1=None, op2=None, verbatim=0, comment=''):
        if self.del_last:
            del self.body[-2:]
            self.del_last=0
            self.curr_bank=self.prelast_bank
            self.instr = self.prelast_instr
            self.prelast_bank=self.last_bank = -1

        self.prelast_instr=self.last_instr
        self.last_instr=self.instr
       #FIXME: more intelligent verbatim code analyzing
        if verbatim:
            for line in cmd.splitlines():
                if line:
                    s=line.split()
                    if s and s[0] != ';':
                        self.last_bank = self.prelast_bank = self.curr_bank = -1
                        break
##        if self.ve:
##            print '%s %s, %s: %i %i %i' % (cmd, op1, op2, self.curr_bank, self.last_bank, self.prelast_bank),
##        if (cmd, op1) == ('clrf', 'PIE2'):
##            print '*****->'
##            self.ve=1
##        if (cmd, op1) == ('movf', '_CLOCK_OSC8'):
##            print '*****<-'
##            self.ve=0
        
        if cmd=='call':
            self.last_bank = self.prelast_bank = self.curr_bank=-1
            
        if verbatim:
            self.body += ['%s\n' % (cmd,)]
            return

        bodys=''
        if comment:
            comment='\t;%s' % comment
        if op1 and (cmd not in self.no_bank_cmds):
##            if self.ve:
##                print '###',
            bodys += self.bank_by_name(op1)

##        if self.ve:
##            print self.curr_bank, self.last_bank, self.prelast_bank
        if len(self.pages) > 1 and op1 and cmd=='call':#(cmd in self.pagesel_cmds):
            #has_dollar=0
            #for ch in op1:
            #    if ch=='$':
            #        has_dollar=1
            #        break
            #if not has_dollar:
                bodys += '\tpagesel %s\n' % op1
                self.instr += 2
            
        if op2 != None:
            bodys += '\t%s\t%s,\t%s' % (cmd, op1, op2)
        elif op1 != None:
            bodys += '\t%s\t%s' % (cmd, op1)
        else:
            bodys += '\t%s' % (cmd,)
        self.instr += 1
        
        if len(self.pages) > 1 and op1 and cmd=='call':#(cmd in self.pagesel_cmds):
            bodys += '\n\tpagesel $+1'
            self.instr += 2


        self.body += [bodys+comment+'\n']

#        if self.instr == self.pages[0][1]:
#            self.say('Program does not fit ROM (maybe because while only first ROM page is supported).')
            
    def get_asm(self):
        return ''.join([self.head] + self.body + [self.tail])

class mem:
    mmap={}
    
    def __init__(self, banks):
        for bank in banks:
            for addr in range(bank[0], bank[1]+1):
                self.mmap[addr] = 1
                
    def reserve_byte(self, addr=None):
        if not len(self.mmap):
            raise 'Program does not fit the RAM!'
        
        if addr == None:
            k=self.mmap.keys()
            k.sort()
            addr=k[0]
        elif not self.mmap.has_key(addr):
            raise 'Address %i is reserved or is not allocatable!' % addr
        
        del self.mmap[addr]
        return addr

    def is_reserved(self, addr):
        return not self.mmap.has_key(addr)
    
    def free_byte(self, addr):
        self.mmap[addr] = 1
