#!/usr/bin/env python

import numpy as np
import sys
import os
import struct
from dataclasses import dataclass


@dataclass
class DataRange:
    start_address: int
    end_address: int
    words: list

@dataclass
class GRPTBL_entry:
    header: int
    n_entries: int
    pointer: int

    @classmethod
    def parse_GRPTBL_entry(cls, words):
        header = words[0]
        n_entries = words[1] >> 4
        pointer = twentybit(words[1], words[2])
        return cls(header, n_entries, pointer)

    def __str__(self):
        header_upper = (self.header >> 8) & 0xff
        header_lower = self.header & 0xff
        return"{:08b} {:08b} n: {:d} pointer: 0o{:06o}".format(header_upper,
                                                               header_lower,
                                                               self.n_entries,
                                                               self.pointer)

@dataclass
class TRUNK_GROUP_entry:
    """Figure 12D"""
    grp_num: int
    mbr: bool
    exists: bool
    highest_member: int
    sel_status_block_index: int
    member_list_index: int
    circuit_code: int

    @classmethod
    def parse_TRUNK_GROUP_entry(cls, grp_num, words):
        mbr = words[0] & 2**8 > 0
        exists = words[0] & 2**7 > 0
        highest_member = words[0] & 0x7f
        sel_status_block_index = words[1] & 0x3fff
        member_list_index = words[2] & 0x3fff
        circuit_code = words[3] & 0x1f
        return cls(grp_num, mbr, exists, highest_member, sel_status_block_index, member_list_index,
                   circuit_code)



def twentybit(a, b):
    return ((a & 0xf) << 16) + b

def load_track(base_filename):

    data_ranges = []

    for block_n in range(0, 358):
        filename = os.path.join(base_filename, "{:04d}.bin".format(block_n))
        try:
            block_data = load_block(filename)
        except FileNotFoundError:
            continue

        next_header = 2
        while(next_header < 828):
            length = (block_data[next_header] & 0xfff0) >> 4
            offset =  ((block_data[next_header] & 0xf) << 16) + block_data[next_header + 1]

            new_range = DataRange(start_address=offset,
                                  end_address=offset+length,
                                  words=block_data[next_header:next_header+length])
            data_ranges.append(new_range)

            next_header += length + 2

            if(length == 0):
                break

    return data_ranges


def load_block(filename):
    f = open(filename, "rb")

    read_len = 50
    word_n = 0
    words = []
    while True:
        data = f.read(2*read_len)
        if(len(data) == 0):
            break
        successful_len = len(data)//2

        new_words = struct.unpack(f'>{successful_len}H', data)

        words.extend(new_words)
    return words

def find_range(target_address, data_ranges):
    for data_range in data_ranges:
        if((target_address >= data_range.start_address) and
           (target_address < data_range.end_address)):
            return data_range

    raise ValueError("Target address not found in data")

def range_starting_at_address(target_address, data_ranges):

    original_range = find_range(target_address, data_ranges)
    offset = target_address - original_range.start_address
    new_range = DataRange(start_address=original_range.start_address + offset,
                          end_address=original_range.end_address,
                          words=original_range.words[offset:])
    return new_range

def print_data(target_address, block, length=5):
    offset = target_address - block.start_address
    if(offset < 0 or offset > (block.end_address - block.start_address)):
       raise ValueError("Target address not found in block")

    for n in range(offset, offset+length):
       print("{:06o}".format(block.words[n]))


if __name__ == '__main__':



    base_filename = "TapeData/1/"
    data = load_track(base_filename)

    if False:
        for data_range in data:
            if(data_range.end_address > data_range.start_address):
                print(data_range.start_address, data_range.end_address,
                      "o{:06o}, o{:06o}".format(data_range.start_address, data_range.end_address))

    #MTI_base = 0o420000
    MTI = 0o421410 + 2

    # MTI_entries = [("GRPTBL", 0o421410)]

    print("------")
    print("MTI:")
    mti_data = range_starting_at_address(MTI, data)

    if False:
        for n in range(0, 20):
           print("{:06o}".format(mti_data.words[n]))


    grptbl_entry_pbx = GRPTBL_entry.parse_GRPTBL_entry(mti_data.words)
    grptbl_entry_svc = GRPTBL_entry.parse_GRPTBL_entry(mti_data.words[3:])
    grptbl_entry_trunks_low = GRPTBL_entry.parse_GRPTBL_entry(mti_data.words[6:])
    grptbl_entry_trunks_high = GRPTBL_entry.parse_GRPTBL_entry(mti_data.words[9:])
    print("PBX/MLHG ", grptbl_entry_pbx)
    print("SVC CKTS ", grptbl_entry_svc)
    print("TRUNK GROUPS 128-191 ", grptbl_entry_trunks_low)
    print("TRUNK GROUPS 192-255 ", grptbl_entry_trunks_high)



    trunk_groups_128 = range_starting_at_address(grptbl_entry_trunks_low.pointer, data)

    for n in range(0, grptbl_entry_trunks_low.n_entries):
        arbitrary_offset = 2
        pointer = grptbl_entry_trunks_low.pointer + arbitrary_offset + (8*n)
        trunk_data_range = range_starting_at_address(pointer, data)
        group_entry = TRUNK_GROUP_entry.parse_TRUNK_GROUP_entry(128 + n, trunk_data_range.words)
        print(group_entry)





