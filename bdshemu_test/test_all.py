#
# Copyright (c) 2020 Bitdefender
# SPDX-License-Identifier: Apache-2.0
#
import os
import sys
import glob
from zipfile import ZipFile
from pathlib import Path

total_tests = 0
failed_tests = 0

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

            print(f'    * Running test case {f}...')
            os.system(f'disasm -shemu {mod} -f {f} >{f}.temp')
            try:
                res = open(f'{f}.result').read()
            except:
                print(f'    ! No result file provided for test {f}!')

            try:
                tmp = open(f'{f}.temp').read()
            except:
                print(f'    ! No result produced by test {f}!')

            total_tests += 1
            if res != tmp:
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

            print(f'    * Regenerating test case {f}...')
            os.system(f'disasm -exi -shemu {mod} -f {f} >{f}.result')

    for f in glob.glob('%s\\*_decoded.bin' % dir):
        os.remove(f)    

cleanup_files = []

print("Extracting test archive...\n")
with ZipFile('bdshemu_test.zip') as zf:
    cleanup_files = zf.namelist()
    zf.extractall(pwd=b'infected')
print("Done!\n")    

for dn in glob.glob("*"):
    if not os.path.isdir(dn):
        continue
    print(f'Testing {dn}...')
    test_dir(dn)
print("Ran %d tests, %d failed" % (total_tests, failed_tests))

print("Cleaning up test files...\n")
for f in cleanup_files:
    p = Path(os.getcwd()) / f
    if p.is_file():
        p.unlink()
print("Done!\n")
