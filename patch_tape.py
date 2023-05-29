#!/usr/bin/env python

import struct
import sys
import os
import argparse
import textwrap
from dataclasses import dataclass

# Patches are word location, original word, then new word
# Position is 1-indexed from the first real word, preamble not counted.

# Track 1 block 0001
patches = [(269, 0o103024, 0o153520),
           (270, 0o031000, 0o010410)
           ]

@dataclass
class MemoryPatch:
    location: int
    old_value: int
    new_value: int
    comment: str = ""

@dataclass
class MemoryBlock:
    location: int
    length: int
    offset_in_block: int

help_string = textwrap.dedent('''
    Replace specific words in ESS tape blocks

    Patch file must be formatted with all values in OCTAL as:
    memory location, old word, new word, comment

    Lines starting with # are ignored.
    ''')


def parse_patch_file(patch_file):
    '''
    Return a list of MemoryPatch objects from a supplied patch file.
    '''
    patches = []

    for line in f:
        if(line.startswith("#")):
            continue

        splits = line.split(',')

        if(len(splits) < 3):
            raise ValueError(f"Patch file line cannot be parsed: {line}")

        patch = MemoryPatch(location=int(splits[0], 8),
                            old_value=int(splits[1], 8),
                            new_value=int(splits[2], 8))
        patches.append(patch)
    return patches


def load_block_data(block_file):
    '''
    '''
    read_len = 50
    words_list = []
    while True:
        data = block_file.read(2*read_len)
        if(len(data) == 0):
            break
        successful_len = len(data)//2

        unpacked_data = struct.unpack(f'>{successful_len}H', data)

        for word in unpacked_data:
            words_list.append(word)

    return words_list

def find_block_destinations(block_data):
    '''
    Return a list of MemoryBlock objects with destination locations and lengths for each block of
    data in the tape block.
    '''
    next_header = 2

    block_infos = []

    while(next_header < 828):
        length = (block_data[next_header] & 0xfff0) >> 4
        location =  ((block_data[next_header] & 0xf) << 16) + block_data[next_header + 1]
        if(length == 0):
            break


        block_info = MemoryBlock(location=location, length=length,
                                 offset_in_block=next_header + 2)
        block_infos.append(block_info)

        next_header += length + 2

    return block_infos



def find_patch(word_n, patches):
    return list(filter(lambda x: x[0] == word_n, patches))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                    description=help_string)

    parser.add_argument("track_directory",
                        help="Directory containing the data for a specific track")
    parser.add_argument("patch_filename", help="File with list of words to patch")

    args = parser.parse_args()

    with open(args.patch_filename) as f:
        patches = parse_patch_file(f)

    if(len(patches) == 0):
        print("No patches provided, exiting")
        sys.exit(0)

    for block_n in range(0, 358):
        block_filename = os.path.join(args.track_directory, "{:04d}.bin".format(block_n))

        try:
            with open(block_filename, 'rb') as f:
                block_data = load_block_data(f)
        except FileNotFoundError:
            print(f"Block file {block_filename} not found, skipping")
            continue

        block_dests = find_block_destinations(block_data)

        for patch in patches:
            for block in block_dests:
                if(patch.location >= block.location and
                   patch.location < (block.location + block.length)):
                    print(f"Found patch destination {patch.location:o}, block {block_n}")





