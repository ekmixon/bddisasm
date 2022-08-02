#!/usr/bin/env python3
#
# Copyright (c) 2020 Bitdefender
# SPDX-License-Identifier: Apache-2.0
#
import os
import sys
import re
import copy
import glob
import disasmlib


flags = {
    'MODRM'    : 'ND_FLAG_MODRM',
    'II64'     : 'ND_FLAG_I64',
    'F64'      : 'ND_FLAG_F64',
    'D64'      : 'ND_FLAG_D64',
    'O64'      : 'ND_FLAG_O64',
    'SSECONDB' : 'ND_FLAG_SSE_CONDB',
    'COND'     : 'ND_FLAG_COND',
    'VSIB'     : 'ND_FLAG_VSIB',
    'MIB'      : 'ND_FLAG_MIB',
    'LIG'      : 'ND_FLAG_LIG',
    'WIG'      : 'ND_FLAG_WIG',
    '3DNOW'    : 'ND_FLAG_3DNOW',
    'MMASK'    : 'ND_FLAG_MMASK',
    'NOMZ'     : 'ND_FLAG_NOMZ',
    'LOCKSP'   : 'ND_FLAG_LOCK_SPECIAL',
    'NOL0'     : 'ND_FLAG_NOL0',
    'NOA16'    : 'ND_FLAG_NOA16',
    'NO66'     : 'ND_FLAG_NO66',
    'NORIPREL' : 'ND_FLAG_NO_RIP_REL',
    'VECT'     : 'ND_FLAG_VECTOR',
    'S66'      : 'ND_FLAG_S66',
    'BITBASE'  : 'ND_FLAG_BITBASE',
    'AG'       : 'ND_FLAG_AG',
    'SHS'      : 'ND_FLAG_SHS',
    'MFR'      : 'ND_FLAG_MFR',
    'CETT'     : 'ND_FLAG_CETT',
    'SERIAL'   : 'ND_FLAG_SERIAL',
    'SIBMEM'   : 'ND_FLAG_SIBMEM',
    'I67'      : 'ND_FLAG_I67',
    'IER'      : 'ND_FLAG_IER',
    'IWO64'    : 'ND_FLAG_IWO64',
}

prefixes_map = {
    'REP'      : 'ND_PREF_REP',
    'REPC'     : 'ND_PREF_REPC',
    'HLE'      : 'ND_PREF_HLE',
    'BND'      : 'ND_PREF_BND',
    'LOCK'     : 'ND_PREF_LOCK',
    'BH'       : 'ND_PREF_BHINT',
    'XACQUIRE' : 'ND_PREF_XACQUIRE',
    'XRELEASE' : 'ND_PREF_XRELEASE',
    'HLEWOL'   : 'ND_PREF_HLE_WO_LOCK',
    'DNT'      : 'ND_PREF_DNT',
}

decorators_map = {
    'MASK'     : 'ND_DECO_MASK',
    'BROADCAST': 'ND_DECO_BROADCAST',
    'ZERO'     : 'ND_DECO_ZERO',
    'SAE'      : 'ND_DECO_SAE',
    'ER'       : 'ND_DECO_ER',
}

# Per operand flags.
opflags = {
    'OPDEF'    : 'ND_OPF_DEFAULT',           # Default operand. Not encoded anywhere.
    'OPSEXO1'  : 'ND_OPF_SEX_OP1',
    'OPSEXDW'  : 'ND_OPF_SEX_DWS',
}

# Explicit operands map.
optype = {
    'A'        : 'ND_OPT_A',
    'B'        : 'ND_OPT_B',
    'C'        : 'ND_OPT_C',
    'D'        : 'ND_OPT_D',
    'E'        : 'ND_OPT_E',
    'F'        : 'ND_OPT_F',
    'G'        : 'ND_OPT_G',
    'H'        : 'ND_OPT_H',
    'I'        : 'ND_OPT_I',
    'J'        : 'ND_OPT_J',
    'K'        : 'ND_OPT_K',
    'L'        : 'ND_OPT_L',
    'M'        : 'ND_OPT_M',
    'N'        : 'ND_OPT_N',
    'O'        : 'ND_OPT_O',
    'P'        : 'ND_OPT_P',
    'Q'        : 'ND_OPT_Q',
    'R'        : 'ND_OPT_R',
    'S'        : 'ND_OPT_S',
    'T'        : 'ND_OPT_T',
    'U'        : 'ND_OPT_U',
    'V'        : 'ND_OPT_V',
    'W'        : 'ND_OPT_W',
    'X'        : 'ND_OPT_X',
    'Y'        : 'ND_OPT_Y',
    'Z'        : 'ND_OPT_Z',
    'rB'       : 'ND_OPT_rB',
    'mB'       : 'ND_OPT_mB',
    'rK'       : 'ND_OPT_rK',
    'vK'       : 'ND_OPT_vK',
    'mK'       : 'ND_OPT_mK',
    'aK'       : 'ND_OPT_aK',
    'rM'       : 'ND_OPT_rM',
    'mM'       : 'ND_OPT_mM',
    'rT'       : 'ND_OPT_rT',
    'mT'       : 'ND_OPT_mT',
    'vT'       : 'ND_OPT_vT',

    # Implicit operands.
    '1'        : 'ND_OPT_CONST_1',
    'AH'       : 'ND_OPT_GPR_AH',
    'rAX'      : 'ND_OPT_GPR_rAX',
    'rCX'      : 'ND_OPT_GPR_rCX',
    'rDX'      : 'ND_OPT_GPR_rDX',
    'rBX'      : 'ND_OPT_GPR_rBX',
    'rSP'      : 'ND_OPT_GPR_rSP',
    'rBP'      : 'ND_OPT_GPR_rBP',
    'rSI'      : 'ND_OPT_GPR_rSI',
    'rDI'      : 'ND_OPT_GPR_rDI',
    'rR8'      : 'ND_OPT_GPR_rR8',
    'rR9'      : 'ND_OPT_GPR_rR9',
    'rR11'     : 'ND_OPT_GPR_rR11',
    'rIP'      : 'ND_OPT_RIP',
    'CS'       : 'ND_OPT_SEG_CS',
    'SS'       : 'ND_OPT_SEG_SS',
    'DS'       : 'ND_OPT_SEG_DS',
    'ES'       : 'ND_OPT_SEG_ES',
    'FS'       : 'ND_OPT_SEG_FS',
    'GS'       : 'ND_OPT_SEG_GS',
    'ST(0)'    : 'ND_OPT_FPU_ST0',
    'ST(i)'    : 'ND_OPT_FPU_STX',
    'XMM0'     : 'ND_OPT_SSE_XMM0',
    'XMM1'     : 'ND_OPT_SSE_XMM1',
    'XMM2'     : 'ND_OPT_SSE_XMM2',
    'XMM3'     : 'ND_OPT_SSE_XMM3',
    'XMM4'     : 'ND_OPT_SSE_XMM4',
    'XMM5'     : 'ND_OPT_SSE_XMM5',
    'XMM6'     : 'ND_OPT_SSE_XMM6',
    'XMM7'     : 'ND_OPT_SSE_XMM7',

    # Memory operands
    'pAX'      : 'ND_OPT_MEM_rAX',
    'pCX'      : 'ND_OPT_MEM_rCX',
    'pBXAL'    : 'ND_OPT_MEM_rBX_AL',
    'pDI'      : 'ND_OPT_MEM_rDI',
    'SHS'      : 'ND_OPT_MEM_SHS',
    'SHS0'     : 'ND_OPT_MEM_SHS0',
    'SHSP'     : 'ND_OPT_MEM_SHSP',

    # Special immediates.
    'm2zI'     : 'ND_OPT_Im2z',
    
    # System registers, MSRs, XCRs, etc.
    'GDTR'     : 'ND_OPT_SYS_GDTR',
    'IDTR'     : 'ND_OPT_SYS_IDTR',
    'LDTR'     : 'ND_OPT_SYS_LDTR',
    'TR'       : 'ND_OPT_SYS_TR',
    'CR0'      : 'ND_OPT_CR_0',
    'XCR'      : 'ND_OPT_XCR',
    'XCR0'     : 'ND_OPT_XCR_0',
    'MSR'      : 'ND_OPT_MSR',
    'FSBASE'   : 'ND_OPT_MSR_FSBASE',
    'GSBASE'   : 'ND_OPT_MSR_GSBASE',
    'KGSBASE'  : 'ND_OPT_MSR_KGSBASE',
    'SCS'      : 'ND_OPT_MSR_SCS',
    'SEIP'     : 'ND_OPT_MSR_SEIP',
    'SESP'     : 'ND_OPT_MSR_SESP',
    'TSC'      : 'ND_OPT_MSR_TSC',
    'TSCAUX'   : 'ND_OPT_MSR_TSCAUX',
    'STAR'     : 'ND_OPT_MSR_STAR',
    'LSTAR'    : 'ND_OPT_MSR_LSTAR',
    'FMASK'    : 'ND_OPT_MSR_FMASK',
    'BANK'     : 'ND_OPT_REG_BANK',
    'X87CONTROL':'ND_OPT_X87_CONTROL',
    'X87TAG'   : 'ND_OPT_X87_TAG',
    'X87STATUS': 'ND_OPT_X87_STATUS',
    'MXCSR'    : 'ND_OPT_MXCSR',
    'PKRU'     : 'ND_OPT_PKRU',
    'SSP'      : 'ND_OPT_SSP',
    'UIF'      : 'ND_OPT_UIF'
}

opsize = {
    'a'        : 'ND_OPS_a', 
    'b'        : 'ND_OPS_b',
    'c'        : 'ND_OPS_c',
    'd'        : 'ND_OPS_d',
    'dq'       : 'ND_OPS_dq',
    'e'        : 'ND_OPS_e',
    'f'        : 'ND_OPS_f',
    'h'        : 'ND_OPS_h',
    'n'        : 'ND_OPS_n',
    'u'        : 'ND_OPS_u',
    'vm32x'    : 'ND_OPS_vm32x',
    'vm32y'    : 'ND_OPS_vm32y',
    'vm32z'    : 'ND_OPS_vm32z',
    'vm32h'    : 'ND_OPS_vm32h',
    'vm32n'    : 'ND_OPS_vm32n',
    'vm64x'    : 'ND_OPS_vm64x',
    'vm64y'    : 'ND_OPS_vm64y',
    'vm64z'    : 'ND_OPS_vm64z',
    'vm64h'    : 'ND_OPS_vm64h',
    'vm64n'    : 'ND_OPS_vm64n',
    'mib'      : 'ND_OPS_mib',
    'v2'       : 'ND_OPS_v2',
    'v3'       : 'ND_OPS_v3',
    'v4'       : 'ND_OPS_v4',
    'v5'       : 'ND_OPS_v5',
    'v8'       : 'ND_OPS_v8',
    'oq'       : 'ND_OPS_oq',
    'p'        : 'ND_OPS_p',
    'pd'       : 'ND_OPS_pd',
    'ps'       : 'ND_OPS_ps',
    'ph'       : 'ND_OPS_ph',
    'q'        : 'ND_OPS_q',
    'qq'       : 'ND_OPS_qq',
    's'        : 'ND_OPS_s',
    'sd'       : 'ND_OPS_sd',
    'ss'       : 'ND_OPS_ss',
    'sh'       : 'ND_OPS_sh',
    'v'        : 'ND_OPS_v',
    'w'        : 'ND_OPS_w',
    'x'        : 'ND_OPS_x',
    'y'        : 'ND_OPS_y',
    'yf'       : 'ND_OPS_yf',
    'z'        : 'ND_OPS_z',
    '?'        : 'ND_OPS_unknown',
    '0'        : 'ND_OPS_0',
    'asz'      : 'ND_OPS_asz',
    'ssz'      : 'ND_OPS_ssz',
    'fa'       : 'ND_OPS_fa',
    'fw'       : 'ND_OPS_fw',
    'fd'       : 'ND_OPS_fd',
    'fq'       : 'ND_OPS_fq',
    'ft'       : 'ND_OPS_ft',
    'fe'       : 'ND_OPS_fe',
    'fs'       : 'ND_OPS_fs',
    'l'        : 'ND_OPS_l',
    'rx'       : 'ND_OPS_rx',
    'cl'       : 'ND_OPS_cl',
    '12'       : 'ND_OPS_12',
    't'        : 'ND_OPS_t',
    '384'      : 'ND_OPS_384',
    '512'      : 'ND_OPS_512',
}

opdecorators = {
    '{K}'      : 'ND_OPD_MASK',
    '{z}'      : 'ND_OPD_Z',
    '{sae}'    : 'ND_OPD_SAE',
    '{er}'     : 'ND_OPD_ER',
    '|B32'     : 'ND_OPD_B32',
    '|B64'     : 'ND_OPD_B64',
    '|B16'     : 'ND_OPD_B16',
}

accessmap = {
    'R'        : 'ND_OPA_R',
    'W'        : 'ND_OPA_W',
    'CR'       : 'ND_OPA_CR',
    'CW'       : 'ND_OPA_CW',
    'RW'       : 'ND_OPA_RW',
    'RCW'      : 'ND_OPA_RCW',
    'CRW'      : 'ND_OPA_CRW',
    'CRCW'     : 'ND_OPA_CRCW',
    'P'        : 'ND_OPA_P',
    'N'        : 'ND_OPA_N',
}

tuples = {
    None    : '0',
    'fv'    : 'ND_TUPLE_FV',
    'hv'    : 'ND_TUPLE_HV',
    'qv'    : 'ND_TUPLE_QV',
    'fvm'   : 'ND_TUPLE_FVM',
    'hvm'   : 'ND_TUPLE_HVM',
    'qvm'   : 'ND_TUPLE_QVM',
    'ovm'   : 'ND_TUPLE_OVM',
    'dup'   : 'ND_TUPLE_DUP',
    'm128'  : 'ND_TUPLE_M128',
    't1s8'  : 'ND_TUPLE_T1S8',
    't1s16' : 'ND_TUPLE_T1S16',
    't1s'   : 'ND_TUPLE_T1S',
    't1f'   : 'ND_TUPLE_T1F',
    't2'    : 'ND_TUPLE_T2',
    't4'    : 'ND_TUPLE_T4',
    't8'    : 'ND_TUPLE_T8',
    't1_4x' : 'ND_TUPLE_T1_4X',
}

extype = {
    None    : '0',

    # SSE/AVX
    '1'     : 'ND_EXT_1',
    '2'     : 'ND_EXT_2',
    '3'     : 'ND_EXT_3',
    '4'     : 'ND_EXT_4',
    '5'     : 'ND_EXT_5',
    '6'     : 'ND_EXT_6',
    '7'     : 'ND_EXT_7',
    '8'     : 'ND_EXT_8',
    '9'     : 'ND_EXT_9',
    '10'    : 'ND_EXT_10',
    '11'    : 'ND_EXT_11',
    '12'    : 'ND_EXT_12',
    '13'    : 'ND_EXT_13',
    
    # EVEX
    'E1'    : 'ND_EXT_E1',
    'E1NF'  : 'ND_EXT_E1NF',
    'E2'    : 'ND_EXT_E2',
    'E3'    : 'ND_EXT_E3',
    'E3NF'  : 'ND_EXT_E3NF',
    'E4'    : 'ND_EXT_E4',
    'E4S'   : 'ND_EXT_E4S',
    'E4nb'  : 'ND_EXT_E4nb',
    'E4NF'  : 'ND_EXT_E4NF',
    'E4NFnb': 'ND_EXT_E4NFnb',
    'E5'    : 'ND_EXT_E5',
    'E5NF'  : 'ND_EXT_E5NF',
    'E6'    : 'ND_EXT_E6',
    'E6NF'  : 'ND_EXT_E6NF',
    'E7NM'  : 'ND_EXT_E7NM',
    'E9'    : 'ND_EXT_E9',
    'E9NF'  : 'ND_EXT_E9NF',
    'E10'   : 'ND_EXT_E10',
    'E10S'  : 'ND_EXT_E10S',
    'E10NF' : 'ND_EXT_E10NF',
    'E11'   : 'ND_EXT_E11',
    'E12'   : 'ND_EXT_E12',
    'E12NP' : 'ND_EXT_E12NP',

    # Opmask
    'K20'   : 'ND_EXT_K20',
    'K21'   : 'ND_EXT_K21',

    # AMX
    'AMX_E1': 'ND_EXT_AMX_E1',
    'AMX_E2': 'ND_EXT_AMX_E2',
    'AMX_E3': 'ND_EXT_AMX_E3',
    'AMX_E4': 'ND_EXT_AMX_E4',
    'AMX_E5': 'ND_EXT_AMX_E5',
    'AMX_E6': 'ND_EXT_AMX_E6',
}

modes = {
    'r0'        : 'ND_MOD_R0',
    'r1'        : 'ND_MOD_R1',
    'r2'        : 'ND_MOD_R2',
    'r3'        : 'ND_MOD_R3',
    'real'      : 'ND_MOD_REAL',
    'v8086'     : 'ND_MOD_V8086',
    'prot'      : 'ND_MOD_PROT',
    'compat'    : 'ND_MOD_COMPAT',
    'long'      : 'ND_MOD_LONG',
    'smm'       : 'ND_MOD_SMM',
    'smm_off'   : 'ND_MOD_SMM_OFF',
    'sgx'       : 'ND_MOD_SGX',
    'sgx_off'   : 'ND_MOD_SGX_OFF',
    'tsx'       : 'ND_MOD_TSX',
    'tsx_off'   : 'ND_MOD_TSX_OFF',
    'vmxr'      : 'ND_MOD_VMXR',
    'vmxn'      : 'ND_MOD_VMXN',
    'vmxr_seam' : 'ND_MOD_VMXR_SEAM',
    'vmxn_seam' : 'ND_MOD_VMXN_SEAM',
    'vmx_off'   : 'ND_MOD_VMX_OFF',
}

indexes = {
    "root"  : 0,
    "None"  : 0,
    None    : 0,

    # modrm.mod
    "mem"   : 0,
    "reg"   : 1,

    # mandatory prefixes
    "NP"    : 0,
    "66"    : 1,
    "F3"    : 2,
    "F2"    : 3,

    # other prefixes
    "rexb"  : 1,
    "rexw"  : 2,
    "64"    : 3,
    "aF3"   : 4,
    "rep"   : 5,
    "sib"   : 6,
    
    # Mode
    "m16"   : 1,
    "m32"   : 2,
    "m64"   : 3,
    
    # Default data size
    "ds16"  : 1,
    "ds32"  : 2,
    "ds64"  : 3,
    "dds64" : 4,
    "fds64" : 5,

    # Default address size
    "as16"  : 1,
    "as32"  : 2,
    "as64"  : 3,

    # Vendor redirection.
    "any"   : 0,
    "intel" : 1,
    "amd"   : 2,
    "geode" : 3,
    "cyrix" : 4,

    # Feature redirection.
    "mpx"   : 1,
    "cet"   : 2,
    "cldm"  : 3,
}

ilut = {
    "root" :            ("ND_ILUT_ROOT",            1,      "ND_TABLE"),
    "opcode" :          ("ND_ILUT_OPCODE",          256,    "ND_TABLE_OPCODE"),
    "opcode_3dnow" :    ("ND_ILUT_OPCODE_3DNOW",    256,    "ND_TABLE_OPCODE"),
    "modrmmod" :        ("ND_ILUT_MODRM_MOD",       2,      "ND_TABLE_MODRM_MOD"),
    "modrmmodpost" :    ("ND_ILUT_MODRM_MOD",       2,      "ND_TABLE_MODRM_MOD"),
    "modrmreg" :        ("ND_ILUT_MODRM_REG",       8,      "ND_TABLE_MODRM_REG"),
    "modrmrm" :         ("ND_ILUT_MODRM_RM",        8,      "ND_TABLE_MODRM_RM"),
    "mprefix" :         ("ND_ILUT_MAN_PREFIX",      4,      "ND_TABLE_MPREFIX"),
    "mode" :            ("ND_ILUT_MODE",            4,      "ND_TABLE_MODE"),
    "dsize" :           ("ND_ILUT_DSIZE",           6,      "ND_TABLE_DSIZE"),
    "asize" :           ("ND_ILUT_ASIZE",           4,      "ND_TABLE_ASIZE"),
    "auxiliary" :       ("ND_ILUT_AUXILIARY",       6,      "ND_TABLE_AUXILIARY"),
    "vendor" :          ("ND_ILUT_VENDOR",          6,      "ND_TABLE_VENDOR"),
    "feature" :         ("ND_ILUT_FEATURE",         4,      "ND_TABLE_FEATURE"),
    "mmmmm" :           ("ND_ILUT_VEX_MMMMM",       32,     "ND_TABLE_VEX_MMMMM"),
    "pp" :              ("ND_ILUT_VEX_PP",          4,      "ND_TABLE_VEX_PP"),
    "l" :               ("ND_ILUT_VEX_L",           4,      "ND_TABLE_VEX_L"),
    "w" :               ("ND_ILUT_VEX_W",           2,      "ND_TABLE_VEX_W"),
    "wi" :              ("ND_ILUT_VEX_WI",          2,      "ND_TABLE_VEX_W"),
}


mnemonics = []
mnemonics_prefix = []

instructions = []
prefixes = []
features = []


#
# Convert one operand into it's C/C++ representation.
#
def cdef_operand(self):
    return "OP(%s, %s, %s, %s, %s, %d)" % (optype[self.Type], opsize[self.Size], \
           '|'.join([opflags[x] for x in self.Flags]) or '0', accessmap[self.Access],   \
           '|'.join([opdecorators[x] for x in self.Decorators]) or 0, self.Block)

disasmlib.Operand.cdef = cdef_operand


#
# Convert one instruction into it's C/C++ representation.
#
def cdef_instruction(self):
    c = ''

    c += '    // Pos:%d Instruction:"%s" Encoding:"%s"/"%s"\n' % \
            (self.Icount, self.__str__(), self.RawEnc, ''.join([x.Encoding for x in self.ExpOps]).replace('S', ''))

    c += '    {\n        '

    # Add the instruction class
    c += f'ND_INS_{self.Class}, '

    # Add the instruction type
    c += f'ND_CAT_{self.Category}, '

    # Add the instruction set
    c += f'ND_SET_{self.Set}, '

    # Add the mneomonic index.
    c += '%d, ' % (mnemonics.index(self.Mnemonic))

    c += '\n        '

    # Add the prefixes map.
    c += '|'.join([prefixes_map[x] for x in self.Prefmap] or '0') + ', '

    c += '\n        '

    all = all(m in self.Modes for m in modes)
    c += 'ND_MOD_ANY, ' if all else '|'.join([modes[m] for m in self.Modes]) + ', '
    c += '\n        '

    # Add the decorators map.
    c += '|'.join([decorators_map[x] for x in self.DecoFlags] or '0') + ', '

    # Add the tuple type and the explicit operands count.
    c += 'ND_OPS_CNT(%d, %d), ' % (len(self.ExpOps), len(self.ImpOps))

    exclass = None
    if self.ExClass:
        if self.ExClass in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13']:
            exclass = 'ND_EXC_SSE_AVX'
        elif self.ExClass in ['K20', 'K21']:
            exclass = 'ND_EXC_OPMASK'
        elif self.ExClass.startswith('AMX_'):
            exclass = 'ND_EXC_AMX'
        else:
            exclass = 'ND_EXC_EVEX'

    c += f'{tuples[self.Tuple]}, ' if self.Evex else '0, '
    # Store exception type & class, if any.
    c += f'{extype[self.ExClass]}, {exclass}, ' if exclass else '0, 0, '
    # Add the FPU flags access, if the instruction is fpu.
    if self.Set == 'X87':
        value = 0
        acc = { '0': 0, '1': 1, 'm': 2, 'u': 3 }
        for i in range(4):
            value |= acc[self.FpuFlags[i]] << (i * 2)
        c += '0x%02x, ' % value
    else:
        c += '0, '

    # The 2 reserved fields.
    c += '0, 0, '

    # Add the instruction flags
    fs = '|'.join([flags[x] for x in self.Flags if x != 'nil' and not x.startswith('OP1') and not x.startswith('OP2')\
                                                              and not x.startswith('OP3') and not x.startswith('OP4')\
                                                              and not x.startswith('OP5') and not x.startswith('OP6')\
                                                                ]) or 0

    c += f'{fs}, '

    # Store the CPUID flag, if any
    flg = "0"
    for feat in features:
        if feat.Name == self.Id:
            flg = f"ND_CFF_{feat.Name}"
    c += f"{flg}, "

    # Store the accessed flags, if any.
    for m in ['t', 'm', '1', '0']:
        flg = "0"
        dst = self.RevFlagsAccess[m]
        if m in ['1', '0']:
            dst = dst + self.RevFlagsAccess['u']
        for f in dst:
            flg += f'|NDR_RFLAG_{f.upper()}'
        c += "\n        %s," % flg

    # Add the instruction operands
    allOps = self.ExpOps + self.ImpOps
    c += "\n        {"
    if allOps:
        for op in self.ExpOps + self.ImpOps:
            c += "\n            " + op.cdef() + ", "
    else:
        c += "\n            0 "
    c += "\n        },"

    c += '\n    }'

    return c

disasmlib.Instruction.cdef = cdef_instruction


#
# Initially, t is an empty hash-table.
#
def group_instructions(ilist):
    d = { }
    is3dnow = False
    priorities = ["opcode", "vendor", "feature", "modrmmod", "modrmreg", "modrmmodpost", "modrmrm", "mprefix", "mode", \
                  "dsize", "asize", "auxiliary", "_"]

    for i in ilist:
        if '3DNOW' in i.Flags:
            is3dnow = True
        else:
            is3dnow = False
            
        if i.Spec["opcodes"]:
            if is3dnow:
                d["__TYPE__"] = "opcode_3dnow"
            else:
                d["__TYPE__"] = "opcode"
        elif i.Spec["mpre"] and i.ModrmRedirAfterMpref:
            if "__TYPE__" not in d or d["__TYPE__"] in priorities[-1:]:
                d["__TYPE__"] = "mprefix" 
        elif i.Spec["vendor"]:
            if "__TYPE__" not in d or d["__TYPE__"] in priorities[-11:]:
                d["__TYPE__"] = "vendor"
        elif i.Spec["feature"]:
            if "__TYPE__" not in d or d["__TYPE__"] in priorities[-10:]:
                d["__TYPE__"] = "feature"
        elif i.Spec["modrm"]["mod"]:
            if "__TYPE__" not in d or d["__TYPE__"] in priorities[-9:]:
                d["__TYPE__"] = "modrmmod"
        elif i.Spec["modrm"]["reg"]:
            if "__TYPE__" not in d or d["__TYPE__"] in priorities[-8:]:
                d["__TYPE__"] = "modrmreg"
        elif i.Spec["modrm"]["modpost"]:
            if "__TYPE__" not in d or d["__TYPE__"] in priorities[-7:]:
                d["__TYPE__"] = "modrmmodpost"
        elif i.Spec["modrm"]["rm"]:
            if "__TYPE__" not in d or d["__TYPE__"] in priorities[-6:]:
                d["__TYPE__"] = "modrmrm"
        elif i.Spec["mpre"]:
            if "__TYPE__" not in d or d["__TYPE__"] in priorities[-5:]:
                d["__TYPE__"] = "mprefix"
        elif i.Spec["mode"]:
            if "__TYPE__" not in d or d["__TYPE__"] in priorities[-4:]:
                d["__TYPE__"] = "mode"
        elif i.Spec["dsize"]:
            if "__TYPE__" not in d or d["__TYPE__"] in priorities[-3:]:
                d["__TYPE__"] = "dsize"
        elif i.Spec["asize"]:
            if "__TYPE__" not in d or d["__TYPE__"] in priorities[-2:]:
                d["__TYPE__"] = "asize"
        elif i.Spec["opre"]:
            if "__TYPE__" not in d or d["__TYPE__"] in priorities[-1:]:
                d["__TYPE__"] = "auxiliary"
        elif len(ilist) == 1:
            return ilist[0]


    for i in ilist:
        if d["__TYPE__"] in ["opcode", "opcode_3dnow"]:
            # Opcode redirection, add the next opcode to the hash, and remove it from the spec.
            if int(i.Spec["opcodes"][0], 16) not in d:
                d[int(i.Spec["opcodes"][0], 16)] = [i]
            else:
                d[int(i.Spec["opcodes"][0], 16)].append(i)

            # Remove the opcode for this instruction.
            del i.Spec["opcodes"][0]
        elif d["__TYPE__"] == "modrmmod":
            if not i.Spec["modrm"]["mod"]:
                if "mem" not in d:
                    d["mem"] = [i]
                else:
                    d["mem"].append(i)

                if "reg" not in d:
                    d["reg"] = [copy.deepcopy(i)]
                else:
                    d["reg"].append(copy.deepcopy(i))
            else:
                if i.Spec["modrm"]["mod"] not in d:
                    d[i.Spec["modrm"]["mod"]] = [i]
                else:
                    d[i.Spec["modrm"]["mod"]].append(i)
            # Remove the mod specifier.
            i.Spec["modrm"]["mod"] = None
        elif d["__TYPE__"] == "modrmreg":
            if int(i.Spec["modrm"]["reg"]) not in d:
                d[int(i.Spec["modrm"]["reg"])] = [i]
            else:
                d[int(i.Spec["modrm"]["reg"])].append(i)
            # Remove the reg specifier
            i.Spec["modrm"]["reg"] = None
        elif d["__TYPE__"] == "modrmmodpost":
            if not i.Spec["modrm"]["modpost"]:
                if "mem" not in d:
                    d["mem"] = [i]
                else:
                    d["mem"].append(i)

                if "reg" not in d:
                    d["reg"] = [copy.deepcopy(i)]
                else:
                    d["reg"].append(copy.deepcopy(i))
            else:
                if i.Spec["modrm"]["modpost"] not in d:
                    d[i.Spec["modrm"]["modpost"]] = [i]
                else:
                    d[i.Spec["modrm"]["modpost"]].append(i)
            # Remove the modpost specifier.
            i.Spec["modrm"]["modpost"] = None
        elif d["__TYPE__"] == "modrmrm":
            if int(i.Spec["modrm"]["rm"]) not in d:
                d[int(i.Spec["modrm"]["rm"])] = [i]
            else:
                d[int(i.Spec["modrm"]["rm"])].append(i)
            # Remove the reg specifier
            i.Spec["modrm"]["rm"] = None
        elif d["__TYPE__"] == "mprefix":
            if not i.Spec["mpre"]:
                p = "None"
            else:
                p = i.Spec["mpre"][0]
            if p not in d:
                d[p] = [i]
            else:
                d[p].append(i)
            # Remove the prefix from the list.
            if p != "None":
                del i.Spec["mpre"][0]
        elif d["__TYPE__"] == "mode":
            if not i.Spec["mode"]:
                p = "None"
            else:
                p = i.Spec["mode"][0]
            if p not in d:
                d[p] = [i]
            else:
                d[p].append(i)
            # Remove the auxiliary redirector
            if p != "None":
                del i.Spec["mode"][0]
        elif d["__TYPE__"] == "dsize":
            if not i.Spec["dsize"]:
                p = "None"
            else:
                p = i.Spec["dsize"][0]
            if p not in d:
                d[p] = [i]
            else:
                d[p].append(i)
            # Remove the auxiliary redirector
            if p != "None":
                del i.Spec["dsize"][0]
        elif d["__TYPE__"] == "asize":
            if not i.Spec["asize"]:
                p = "None"
            else:
                p = i.Spec["asize"][0]
            if p not in d:
                d[p] = [i]
            else:
                d[p].append(i)
            # Remove the auxiliary redirector
            if p != "None":
                del i.Spec["asize"][0]
        elif d["__TYPE__"] == "auxiliary":
            if not i.Spec["opre"]:
                p = "None"
            else:
                p = i.Spec["opre"][0]
            if p not in d:
                d[p] = [i]
            else:
                d[p].append(i)
            # Remove the auxiliary redirector
            if p != "None":
                del i.Spec["opre"][0]
        elif d["__TYPE__"] == "vendor":
            if not i.Spec["vendor"]:
                p = "None"
            else:
                p = i.Spec["vendor"]
            if p not in d:
                d[p] = [i]
            else:
                d[p].append(i)
            # Remove the vendor redirector
            if p != "None":
                i.Spec["vendor"] = None
        elif d["__TYPE__"] == "feature":
            if not i.Spec["feature"]:
                p = "None"
            else:
                p = i.Spec["feature"]
            if p not in d:
                d[p] = [i]
            else:
                d[p].append(i)
            # Remove the vendor redirector
            if p != "None":
                i.Spec["feature"] = None
        else:
            print("Don't know what to do!")
            raise Exception("Unknwon redirection type.")

    return d



def group_instructions_vex_xop_evex(ilist):
    d = { }

    for i in ilist:
        if i.Spec["mmmmm"]:
            d["__TYPE__"] = "mmmmm"
        elif i.Spec["opcodes"]:
            if "__TYPE__" not in d or d["__TYPE__"] in ["w", "l", "pp", "modrmrm", "modrmmodpost", "modrmreg", \
                                                        "modrmmod"]:
                d["__TYPE__"] = "opcode"
        elif i.Spec["pp"]:
            if "__TYPE__" not in d or d["__TYPE__"] in ["w", "l", "modrmrm", "modrmmodpost", "modrmreg"]:
                d["__TYPE__"] = "pp"
        elif i.Spec["modrm"]["mod"]:
            if "__TYPE__" not in d or d["__TYPE__"] in ["w", "l", "modrmrm", "modrmmodpost", "modrmreg"]:
                d["__TYPE__"] = "modrmmod"
        elif i.Spec["modrm"]["reg"]:
            if "__TYPE__" not in d or d["__TYPE__"] in ["w", "l", "modrmrm", "modrmmodpost"]:
                d["__TYPE__"] = "modrmreg"
        elif i.Spec["modrm"]["modpost"]:
            if "__TYPE__" not in d or d["__TYPE__"] in ["w", "l", "modrmrm"]:
                d["__TYPE__"] = "modrmmodpost"
        elif i.Spec["modrm"]["rm"]:
            if "__TYPE__" not in d or d["__TYPE__"] in ["w", "l"]:
                d["__TYPE__"] = "modrmrm"
        elif i.Spec["l"]:
            if "__TYPE__" not in d or d["__TYPE__"] in ["w"]:
                d["__TYPE__"] = "l"
        elif i.Spec["w"]:
            if "__TYPE__" not in d:
                if 'IWO64' in i.Flags:
                    d["__TYPE__"] = "wi"
                else:
                    d["__TYPE__"] = "w"
        elif len(ilist) == 1:
            return ilist[0]


    for i in ilist:
        if d["__TYPE__"] == "mmmmm":
            if int(i.Spec["mmmmm"], 16) not in d:
                d[int(i.Spec["mmmmm"], 16)] = [i]
            else:
                d[int(i.Spec["mmmmm"], 16)].append(i)
            i.Spec["mmmmm"] = None
        elif d["__TYPE__"] == "opcode":
            # Opcode redirection, add the next opcode to the hash, and remove it from the spec.
            if int(i.Spec["opcodes"][0], 16) not in d:
                d[int(i.Spec["opcodes"][0], 16)] = [i]
            else:
                d[int(i.Spec["opcodes"][0], 16)].append(i)
            # Remove the opcode for this instruction.
            del i.Spec["opcodes"][0]
        elif d["__TYPE__"] == "modrmmod":
            if not i.Spec["modrm"]["mod"]:
                if "mem" not in d:
                    d["mem"] = [i]
                else:
                    d["mem"].append(i)

                if "reg" not in d:
                    d["reg"] = [copy.deepcopy(i)]
                else:
                    d["reg"].append(copy.deepcopy(i))
            else:
                if i.Spec["modrm"]["mod"] not in d:
                    d[i.Spec["modrm"]["mod"]] = [i]
                else:
                    d[i.Spec["modrm"]["mod"]].append(i)
            # Remove the mod specifier.
            i.Spec["modrm"]["mod"] = None
        elif d["__TYPE__"] == "modrmreg":
            if int(i.Spec["modrm"]["reg"]) not in d:
                d[int(i.Spec["modrm"]["reg"])] = [i]
            else:
                d[int(i.Spec["modrm"]["reg"])].append(i)
            # Remove the reg specifier
            i.Spec["modrm"]["reg"] = None
        elif d["__TYPE__"] == "modrmmodpost":
            if not i.Spec["modrm"]["modpost"]:
                if "mem" not in d:
                    d["mem"] = [i]
                else:
                    d["mem"].append(i)

                if "reg" not in d:
                    d["reg"] = [copy.deepcopy(i)]
                else:
                    d["reg"].append(copy.deepcopy(i))
            else:
                if i.Spec["modrm"]["modpost"] not in d:
                    d[i.Spec["modrm"]["modpost"]] = [i]
                else:
                    d[i.Spec["modrm"]["modpost"]].append(i)
            # Remove the modpost specifier.
            i.Spec["modrm"]["modpost"] = None
        elif d["__TYPE__"] == "modrmrm":
            if int(i.Spec["modrm"]["rm"]) not in d:
                d[int(i.Spec["modrm"]["rm"])] = [i]
            else:
                d[int(i.Spec["modrm"]["rm"])].append(i)
            # Remove the reg specifier
            i.Spec["modrm"]["rm"] = None
        elif d["__TYPE__"] == "pp":
            p = int(i.Spec["pp"])
            if p not in d:
                d[p] = [i]
            else:
                d[p].append(i)
            # Remove the prefix from the list.
            i.Spec["pp"] = None
        elif d["__TYPE__"] == "l":
            p = int(i.Spec["l"])
            if p not in d:
                d[p] = [i]
            else:
                d[p].append(i)
            # Remove the prefix from the list.
            i.Spec["l"] = None
        elif d["__TYPE__"] in ["w", "wi"]:
            p = int(i.Spec["w"])
            if p not in d:
                d[p] = [i]
            else:
                d[p].append(i)
            # Remove the prefix from the list.
            i.Spec["w"] = None
        else:
            print("Don't know what to do!")
            raise Exception("Unknown redirection type.")

    return d


def build_hash_tree2(t, cbk):
    for k in t:
        if type(disasmlib.Instruction) == type(t[k]):
            # Instruction, leaf, we're done.
            continue
        elif type([]) == type(t[k]):
            # List, group the instructions, and recurse.
            t[k] = cbk(t[k])
            
            if type({}) == type(t[k]):
                build_hash_tree2(t[k], cbk)

                
def dump_hash_tree2(t, level = 0):
    if type(t) == type({}):
        for h in t:
            if h == "__TYPE__":
                continue
            print("%s %s (type: %s)" % ("    " * level, h, t["__TYPE__"]))
            dump_hash_tree2(t[h], level + 1)
    else:
        print("    " * level, t)

    
#
#
#
def generate_translations2(instructions):
    table_st = []
    table_xop = []
    table_vex = []
    table_evex = []

    hash_st = {}
    hash_vex = {}
    hash_xop = {}
    hash_evex = {}
    
    # Distribute each instruction type into its own table.
    for i in instructions:
        if i.Vex:
            table_vex.append(i)
        elif i.Xop:
            table_xop.append(i)
        elif i.Evex:
            table_evex.append(i)
        else:
            table_st.append(i)

    hash_st["__TYPE__"] = "root"
    hash_st["root"] = table_st
    build_hash_tree2(hash_st, group_instructions)

    hash_vex["__TYPE__"] = "root"
    hash_vex["root"] = table_vex
    build_hash_tree2(hash_vex, group_instructions_vex_xop_evex)

    hash_xop["__TYPE__"] = "root"
    hash_xop["root"] = table_xop
    build_hash_tree2(hash_xop, group_instructions_vex_xop_evex)

    hash_evex["__TYPE__"] = "root"
    hash_evex["root"] = table_evex
    build_hash_tree2(hash_evex, group_instructions_vex_xop_evex)

    # Dump'em!
    #print "###########################################################################################################"
    #dump_hash_tree2(hash_st)
    print('Writing the table_root.h file...')
    f = open(r'../bddisasm/include/table_root.h', 'wt')
    f.write("#ifndef TABLE_ROOT_H\n")
    f.write("#define TABLE_ROOT_H\n\n")
    dump_translation_tree_c(hash_st, 'gRootTable', f)
    f.write("\n#endif\n\n")
    f.close()
    #print "###########################################################################################################"
    #dump_hash_tree2(hash_vex)
    print('Writing the table_vex.h file...')
    f = open(r'../bddisasm/include/table_vex.h', 'wt')
    f.write("#ifndef TABLE_VEX_H\n")
    f.write("#define TABLE_VEX_H\n\n")
    dump_translation_tree_c(hash_vex, 'gVexTable', f)
    f.write("\n#endif\n\n")
    f.close()
    #print "###########################################################################################################"
    #dump_hash_tree2(hash_xop)
    print('Writing the table_xop.h file...')
    f = open(r'../bddisasm/include/table_xop.h', 'wt')
    f.write("#ifndef TABLE_XOP_H\n")
    f.write("#define TABLE_XOP_H\n\n")
    dump_translation_tree_c(hash_xop, 'gXopTable', f)
    f.write("\n#endif\n\n")
    f.close()
    #print "###########################################################################################################"
    #dump_hash_tree2(hash_evex)
    print('Writing the table_evex.h file...')
    f = open(r'../bddisasm/include/table_evex.h', 'wt')
    f.write("#ifndef TABLE_EVEX_H\n")
    f.write("#define TABLE_EVEX_H\n\n")
    dump_translation_tree_c(hash_evex, 'gEvexTable', f)
    f.write("\n#endif\n\n")
    f.close()
    #print "###########################################################################################################"

    return [hash_st, hash_vex, hash_xop, hash_evex]


def generate_mnemonics(instructions):
    mnemonics = []

    for i in instructions:
        mnemonics.append(i.Mnemonic)

    return sorted(set(mnemonics))

def generate_constants(lst, pre = False):
    constants = []

    for i in lst:
        if pre:
            constants.append('ND_PRE_' + i.Mnemonic)
        else:
            constants.append('ND_INS_' + i.Class)

    return sorted(set(constants))
    
def generate_constants2(instructions):
    constants_sets, constants_types = [], []

    for i in instructions:
        constants_sets.append('ND_SET_' + i.Set)
        constants_types.append('ND_CAT_' + i.Category)

    return sorted(set(constants_sets)), sorted(set(constants_types))

def dump_mnemonics(mnemonics, prefixes, fname):
    f = open(fname, 'wt')
    f.write('#ifndef MNEMONICS_H\n')
    f.write('#define MNEMONICS_H\n')
    f.write('\n')
    f.write('const char *gMnemonics[%d] = \n' % len(mnemonics))
    f.write('{\n')
    f.write('    ')

    i = 0
    ln = 0
    for m in mnemonics:
        f.write('"%s", ' % m)
        ln += len(m) + 4
        i += 1
        if ln > 60:
            ln = 0
            f.write('\n    ')

    f.write('\n};\n\n\n')

    f.write('const char *gPrefixes[%d] = \n' % len(prefixes))
    f.write('{\n')
    f.write('    ')

    i = 0
    for p in prefixes:
        f.write('"%s", ' % p)
        i += 1
        if i % 8 == 0:
            f.write('\n    ')

    f.write('\n};\n\n#endif\n\n')
    f.close()

def dump_constants(constants, prefixes, constants_sets, constants_types, fname):
    f = open(fname, 'wt')
    f.write('//\n')
    f.write('// This file was auto-generated by generate_tables.py from defs.dat. DO NOT MODIFY!\n')
    f.write('//\n\n')
    f.write('#ifndef CONSTANTS_H\n')
    f.write('#define CONSTANTS_H\n\n')
    f.write('\n')
    f.write('typedef enum _ND_INS_CLASS\n')
    f.write('{\n')
    f.write('    ND_INS_INVALID = 0,\n')

    for c in constants:
        f.write('    %s,\n' % c)

    f.write('\n} ND_INS_CLASS;\n\n\n')

    # Now the instruction sets.
    f.write('typedef enum _ND_INS_SET\n')
    f.write('{\n')
    f.write('    ND_SET_INVALID = 0,\n')
    for c in constants_sets:
        f.write('    %s,\n' % c)
    f.write('\n} ND_INS_SET;\n\n\n')
    
    # Now the instruction types.
    f.write('typedef enum _ND_INS_TYPE\n')
    f.write('{\n')
    f.write('    ND_CAT_INVALID = 0,\n')
    for c in constants_types:
        f.write('    %s,\n' % c)
    f.write('\n} ND_INS_CATEGORY;\n\n\n')
    
    # Done!
    f.write('\n#endif\n')
    
    f.close()

def dump_tree(translations, level = 0):
    if type(translations) != type([]):
        print('%s%s' % (level * '    ', translations))
    else:
        for i in range(0, len(translations), 1):
            if len(translations) == 1:
                dump_tree(translations[i], level + 1)
            else:
                dump_tree(translations[i], level + 2)

def generate_master_table(instructions, fname):
    f = open(fname, 'wt')
    f.write('//\n')
    f.write('// This file was auto-generated by generate_tables.py from defs.dat. DO NOT MODIFY!\n')
    f.write('//\n\n')
    f.write('#ifndef INSTRUCTIONS_H\n')
    f.write('#define INSTRUCTIONS_H\n')
    f.write('\n')
    flags = []
    f.write('const ND_INSTRUCTION gInstructions[%s] = \n' % len(instructions))
    f.write('{\n')
    for i in instructions:
        f.write('%s, \n\n' % i.cdef())
    f.write('\n};\n')
    f.write('\n#endif\n')
    f.close()


def dump_translation_tree_c(t, hname, f):
    if type(t) == type({}):
        pointers = []
        
        ttype = t["__TYPE__"]

        for x in range(0, ilut[ttype][1]): pointers.append(None)

        tname = '%s_%s' % (hname, ttype)

        res  = 'const %s %s = \n' % (ilut[ttype][2], tname)
        res += '{\n'
        res += '    %s,\n' % ilut[ttype][0]
        res += '    { \n'

        for h in t:
            if h == "__TYPE__":
                continue

            if type(0) == type(h):
                name = dump_translation_tree_c(t[h], hname + '_%02x' % h, f)
            else:
                name = dump_translation_tree_c(t[h], hname + '_%s' % h, f)

            if ttype in ["opcode", "opcode_3dnow", "mmmmm", "pp", "l", "w", "wi", "modrmreg", "modrmrm"]:
                index = h
            else:
                index = indexes[h]

            try:
                pointers[index] = name
            except:
                print(index, name)
                print("fail fail fail", index)

        i = 0
        for p in pointers:
            if not p:
                res += '        /* %02x */ ND_NULL,\n' % i
            else:
                res += '        /* %02x */ (const void *)&%s,\n' % (i, p)
            i += 1

        res += '    }\n'
        res += '};\n\n'
        
        if ttype == "root":
            f.write("const PND_TABLE %s = (const PND_TABLE)&%s;\n\n" % (hname, name))
        else:
            f.write(res)

        return tname
    else:
        # Instruction, construct a dummy table that directly points to the instruction.
        name = '%s_leaf' % hname
        res  = 'const ND_TABLE_INSTRUCTION %s = \n' % name
        res += '{\n'
        res += '    ND_ILUT_INSTRUCTION,\n'
        res += '    (const void *)&gInstructions[%d]\n' % t.Icount
        res += '};\n\n'
        f.write(res)
        return name

def generate_features(features, fname):
    f = open(fname, 'wt')
    f.write('#ifndef CPUID_FLAGS_H\n')
    f.write('#define CPUID_FLAGS_H\n')

    f.write('\n')
    f.write('#define ND_CFF_NO_LEAF    0xFFFFFFFF\n')
    f.write('#define ND_CFF_NO_SUBLEAF 0x00FFFFFF\n')
    f.write('\n')
    f.write('\n')
    f.write('#define ND_CFF(leaf, subleaf, reg, bit) ((ND_UINT64)(leaf) | ((ND_UINT64)((subleaf) & 0xFFFFFF) << 32) | ((ND_UINT64)(reg) << 56) | ((ND_UINT64)(bit) << 59))\n')
    f.write('\n')

    for c in features:
        f.write('#define ND_CFF_%s%sND_CFF(%s, %s, %s, %s)\n' % (c.Name, ' ' * (25 - len(c.Name)), c.Leaf, c.SubLeaf, 'NDR_' + c.Reg, c.Bit))

    f.write('\n')

    f.write('#endif // CPUID_FLAGS_H\n')

#
# =============================================================================
# Main
# =============================================================================
#
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: %s defs-file' % os.path.basename(sys.argv[0]))
        sys.exit(-1)

    # Extract the flags.
    print('Loading flags access templates...')
    flagsaccess = disasmlib.parse_flags_file('%s/flags.dat' % sys.argv[1])

    # Extact the CPUID features.
    print('Loading CPUID feature flags templates...')
    features = disasmlib.parse_cff_file('%s/cpuid.dat' % sys.argv[1])

    # Extract the prefixes.
    print('Loading prefixes...')
    prefixes = disasmlib.parse_pre_file('%s/prefixes.dat' % sys.argv[1])

    # Extract the valid modes.
    print('Loading CPU operating modes templates...')
    insmodes = disasmlib.parse_modess_file('%s/modes.dat' % sys.argv[1])

    # Extract the instructions.
    for fn in glob.glob('%s/table*.dat' % sys.argv[1]):
        print('Loading instructions from %s...' % fn)
        instructions = instructions + disasmlib.parse_ins_file(fn, flagsaccess, features, insmodes)

    # Sort the instructions.
    instructions = sorted(instructions, key = lambda x: x.Mnemonic)
    for i in range(0, len(instructions)):
        instructions[i].Icount = i

    # Generate the translation tree
    translations = generate_translations2(instructions)

    # Generate the mnemonics
    mnemonics = generate_mnemonics(instructions)
    mnemonics_prefixes = generate_mnemonics(prefixes)

    # Generate the constants
    constants = generate_constants(instructions)
    constants_prefixes = generate_constants(prefixes, True)
    constants_sets, constants_types = generate_constants2(instructions)

    #
    # Dump all data to files.
    #

    # Dump the mnemonics
    print('Writing the mnemonics.h file...')
    dump_mnemonics(mnemonics, mnemonics_prefixes, r'../bddisasm/include/mnemonics.h')

    # Dump the instruction constants
    print('Writing the constants.h (instruction definitions) file...')
    dump_constants(constants, constants_prefixes, constants_sets, constants_types, r'../inc/constants.h')

    print('Writing the instructions.h (main instruction database) file...')
    generate_master_table(instructions, r'../bddisasm/include/instructions.h')

    print('Writing the cpuidflags.h (CPUID feature flags) file...')
    generate_features(features, r'../inc/cpuidflags.h')

    print('Instruction succesfully parsed & header files generated!')
