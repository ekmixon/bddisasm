#
# Copyright (c) 2020 Bitdefender
# SPDX-License-Identifier: Apache-2.0
#
import os
import sys
import glob

total_tests = 0
failed_tests = 0

def get_dict(ins):
    prefix = ""

    # Remove lines that don't contain tokens.
    lines = ins.split("\n")

    d = {"disasm": lines[0]}
    for line in lines[1:]:
        tokens = line.split(",")
        for t in tokens:
            val = t.split(":")
            if len(val) != 2:
                continue
            a = val[0].strip(" ")
            b = val[1].strip(" ")
            if a == "Operand":
                prefix = f"op{b}_"
            a = prefix + a
            d[a] = b
    return d

def compare_instruction(i1, i2):
    x1 = get_dict(i1)
    x2 = get_dict(i2)
    for t in x1:
        if t not in x2:
            print("    ! ERROR: Token '%s', value '%s' missing from output!" % (t, x1[t]))
            return False
        if x1[t] != x2[t]:
            print("    ! ERROR: Token '%s' value mismatch: expected '%s', got '%s'!" % (t, x1[t], x2[t]))
            return False
    for t in x2:
        if t not in x1:
            print("    ! WARNING: Extra token in result: '%s', value '%s'!" % (t, x2[t]))

    return True

def compare_results(data1, data2):
    ins1 = data1.split("\n\n")
    ins2 = data2.split("\n\n")
    if len(ins1) != len(ins2):
        print("    ! Different number of instructions in output: expected %d, got %d!" % (len(ins1), len(ins2)))
        return False
    for i in range(len(ins1)):
        if not compare_instruction(ins1[i], ins2[i]):
            print("    ! ERROR: Instruction mismatch at %d!" % (i))
            return False
    return True

def test_dir(dir):
    global total_tests
    global failed_tests

    for f in glob.glob('%s\\*' % dir):
        if f.find('.') == -1:
            if f.find('_16') > 0:
                mod = '-b16'
            elif f.find('_32') > 0:
                mod = '-b32'
            else:
                mod = '-b64'
            if f.find('_r0') > 0:
                mod += ' -k'
            if f.find('_skip') > 0:
                mod += ' -skip16'

            print(f'    * Running test case {f}...')
            os.system(f'disasm -exi {mod} -f {f} >{f}.temp')
            try:
                res = open(f'{f}.result').read()
            except:
                print(f'    ! No result file provided for test {f}!')

            try:
                tmp = open(f'{f}.temp').read()
            except:
                print(f'    ! No result produced by test {f}!')

            total_tests += 1
            if not compare_results(res, tmp):
                print('    **** FAILED! ****')
                failed_tests += 1
            else:
                print('    * Passed.')

    for f in glob.glob('%s\\*_decoded.bin' % dir):
        os.remove(f)
    for f in glob.glob('%s\\*.temp' % dir):
        os.remove(f)
        
def regenerate(dir): 
    for f in glob.glob('%s\\*' % dir):
        if f.find('.') == -1:
            if f.find('_16') > 0:
                mod = '-b16'
            elif f.find('_32') > 0:
                mod = '-b32'
            else:
                mod = '-b64'
            if f.find('_r0') > 0:
                mod += ' -k'
            if f.find('_skip') > 0:
                mod += ' -skip16'

            print(f'    * Regenerating test case {f}...')
            os.system(f'disasm -exi {mod} -f {f} >{f}.result')

    for f in glob.glob('%s\\*_decoded.bin' % dir):
        os.remove(f)

for dn in glob.glob("*"):
    if not os.path.isdir(dn):
        continue
    print(f'Testing {dn}...')
    test_dir(dn)
print("Ran %d tests, %d failed" % (total_tests, failed_tests))