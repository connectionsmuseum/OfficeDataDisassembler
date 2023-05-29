#!/usr/bin/env python

import struct
import sys
import os
import argparse
import textwrap
from dataclasses import dataclass

import fastcrc

@dataclass
class MemoryPatch:
    location: int
    old_value: int
    new_value: int
    min_block: int = 0
    max_block: int = 400
    comment: str = ""

@dataclass
class MemoryBlock:
    location: int
    length: int
    offset_in_block: int

help_string = textwrap.dedent('''
    Replace specific words in ESS tape blocks

    Patch file must be formatted with all memory locations and values in OCTAL as:
    memory location, old word, new word, min block, max block, comment

    min and max block locations are optional. These enable patches to
    affect only the translation area while leaving the back office data
    unchanged.

    Lines starting with # are ignored.

    Patched blocks are written to [block_number]_patched.bin. Originals are left in place.
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

        if(len(splits) >= 4):
            patch.min_block = int(splits[3])

        if(len(splits) >= 5):
            patch.max_block = int(splits[4])

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

def write_block(filename, block_data):

    with open(filename, 'wb') as f:
        for word in block_data:
            f.write(struct.pack('>H', word))


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


def compute_block_crc(block_data):

    crc_data = b''.join([x.to_bytes(2, byteorder='little') for x in block_data[1:-2]])

    crc_value = fastcrc.crc16.arc(crc_data)
    return crc_value



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

        found_patches = []
        for patch in patches:
            for memory_block in block_dests:
                if(patch.location >= memory_block.location and
                   patch.location < (memory_block.location + memory_block.length) and
                   block_n >= patch.min_block and
                   block_n < patch.max_block):
                    print(f"Found patch destination {patch.location:o}, tape block {block_n}")
                    found_patches.append((patch, memory_block))

        if(len(found_patches) == 0):
            continue

        prepatch_crc_value = compute_block_crc(block_data)
        block_data_crc = block_data[-2]
        if(prepatch_crc_value != block_data_crc):
            print(f"Pre-patching computed CRC {prepatch_crc_value:06o} does not match block CRC {block_data_crc:06o}, quitting")
            sys.exit(0)

        new_block_data = block_data.copy()
        for patch, memory_block in found_patches:
            offset_in_block = patch.location - memory_block.location + memory_block.offset_in_block
            existing_value = block_data[offset_in_block]
            print(f"Location {patch.location:06o}, existing memory value {existing_value:06o}, expected old value "
                  f"{patch.old_value:06o}, new memory value {patch.new_value:06o}")
            if(existing_value == patch.old_value):
                new_block_data[offset_in_block] = patch.new_value
            else:
                print("Old value does not match expected old value, quitting.")
                sys.exit(0)

        new_crc = compute_block_crc(new_block_data)
        new_block_data[-2] = new_crc
        patched_filename = os.path.join(args.track_directory ,f"{block_n:04d}_patched.bin")
        write_block(patched_filename, new_block_data)

