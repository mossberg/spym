#!/usr/bin/env python2.7

import argparse
import logging as log

from util import parse
from emu.cpu import CPU
from emu.instruction import Instruction
from emu.memory import Memory
from util.assemble import SPYM_MAGIC, SPYM_HDR_LEN, SPYMHeader
from util.misc import get_section


def get_args():
    parser = argparse.ArgumentParser(description='Spym MIPS Interpreter. Starts in interactive shell mode, unless given MIPS source file as argument.')
    parser.add_argument('file', metavar='FILE', type=str,
                        help='MIPS source file', nargs='?')
    parser.add_argument('--stack', type=int, help='Stack memory size. Default: 64 bytes',
                        default=64)
    parser.add_argument('--debug', help='Activate debugger. Implies verbose.',
                        action='store_true')
    parser.add_argument('-v', '--verbose', help='Verbose output',
                        action='store_true')
    return parser.parse_args()


def run_source(raw):
    source = raw.splitlines()
    dseg, tseg = parse.segments(source)
    dmem = Memory(args.stack)
    if dseg:
        dmem.memory = parse.data(dseg) + dmem.memory
    cpu = CPU(dmem, parse.text_list(tseg))
    cpu.start(args.debug)
    cpu.dump()


def run_binary(raw):
    hdr = SPYMHeader(binary=raw[:SPYM_HDR_LEN])
    text = parse.bin2text_list(get_section(raw, hdr.text_off, hdr.text_size))
    dmem = Memory(args.stack)
    dmem.memory = get_section(raw, hdr.data_off, hdr.data_size) + dmem.memory
    cpu = CPU(dmem, text)
    cpu.start(args.debug)
    cpu.dump()




def main():
    global args
    args = get_args()

    if args.file:
        lvl = log.INFO if args.verbose or args.debug else None
        log.basicConfig(format='%(message)s', level=lvl)

        with open(args.file) as f:
            raw = f.read()
            if raw[:4] == SPYM_MAGIC:
                run_binary(raw)
            else:
                run_source(raw)
    else:
        log.basicConfig(format='%(message)s', level=log.INFO)
        cpu = CPU(Memory(args.stack))
        while True:
            inp = raw_input('spym > ').strip()
            if inp == 'exit':
                break
            elif inp == 'dump':
                cpu.dump()
                continue
            elif not inp:
                continue

            try:
                cpu.execute_single(Instruction(inp))
            except Exception as e:
                if e.message == 'exit syscall':
                    break
                raise e

        cpu.dump()

if __name__ == '__main__':
    main()
