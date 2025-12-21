#!/usr/bin/env python

import numpy as np
import sys
import os
import struct
import math
from dataclasses import dataclass

@dataclass
class DataRange:
    start_address: int
    end_address: int
    words: list

    def subset(self, offset, length):
        new_start = self.start_address + offset
        return DataRange(start_address=new_start,
                         end_address=new_start + length,
                         words=self.words[offset:(offset+length)])

    def subset_at_address(self, address, length):

        if address < self.start_address or address + length > self.end_address:
            raise ValueError(f"New addresss 0o{address:06o} not within range 0o{self.start_address:06o}-0o{self.end_address:06o}")

        offset = address - self.start_address

        return DataRange(start_address=address,
                         end_address=address + length,
                         words=self.words[offset:(offset+length)])

@dataclass
class GRPTBL:
    dataRange: DataRange
    pbx_table_address: int
    pbx_table_entry_count: int
    pbx_table_entries: list   #unused

    svc_table_address: int
    svc_table_entry_count: int
    svc_table_entries: list[SERVICE_GROUP_entry]

    trunk_table_low_address: int
    trunk_table_low_entry_count: int
    trunk_table_low_entries: list[TRUNK_GROUP_entry]

    trunk_table_high_address: int
    trunk_table_high_entry_count: int
    trunk_table_high_entries: list[TRUNK_GROUP_entry]

    @classmethod
    def parse_GRPTBL(cls, dataRange: DataRange):

        # grptbl_entry_pbx = GRPTBL_entry.parse_GRPTBL_entry(grptable_data.words)
        # grptbl_entry_svc = GRPTBL_entry.parse_GRPTBL_entry(grptable_data.words[3:])
        # grptbl_entry_trunks_low = GRPTBL_entry.parse_GRPTBL_entry(grptable_data.words[6:])
        # grptbl_entry_trunks_high = GRPTBL_entry.parse_GRPTBL_entry(grptable_data.words[9:])

        def parse_entry(dataRange):
            n_entries = dataRange.words[1] >> 4
            pointer = twentybit(dataRange.words[1], dataRange.words[2])
            return pointer, n_entries

        svc_table_address, svc_table_entry_count = parse_entry(dataRange.subset(3,3))
        svc_table_entries = []
        for n in range(0, svc_table_entry_count):
            group_number = 64 + n
            pointer = svc_table_address + (4*n)
            svc_data_range = dataRange.subset_at_address(pointer, 4)
            group_entry = SERVICE_GROUP_entry.parse(group_number, svc_data_range)
            svc_table_entries.append(group_entry)

        trunk_table_low_address, trunk_table_low_entry_count = parse_entry(dataRange.subset(6,3))
        trunk_table_low_entries = []
        for n in range(0, trunk_table_low_entry_count):
            group_number = 128 + n
            pointer = trunk_table_low_address + (8*n)
            trunk_data_range = dataRange.subset_at_address(pointer, 8)
            group_entry = TRUNK_GROUP_entry.parse(group_number, trunk_data_range)
            trunk_table_low_entries.append(group_entry)

        trunk_table_high_address, trunk_table_high_entry_count = parse_entry(dataRange.subset(9,3))
        trunk_table_high_entries = []
        for n in range(0, trunk_table_high_entry_count):
            group_number = 128 + n
            pointer = trunk_table_high_address + (8*n)
            trunk_data_range = dataRange.subset_at_address(pointer, 8)
            group_entry = TRUNK_GROUP_entry.parse(group_number, trunk_data_range)
            trunk_table_high_entries.append(group_entry)

        return cls(dataRange=dataRange,
                   pbx_table_address=0,
                   pbx_table_entry_count=0,
                   pbx_table_entries=[],
                   svc_table_address=svc_table_address,
                   svc_table_entry_count=svc_table_entry_count,
                   svc_table_entries=svc_table_entries,
                   trunk_table_low_address=trunk_table_low_address,
                   trunk_table_low_entry_count=trunk_table_low_entry_count,
                   trunk_table_low_entries=trunk_table_low_entries,
                   trunk_table_high_address=trunk_table_high_address,
                   trunk_table_high_entry_count=trunk_table_high_entry_count,
                   trunk_table_high_entries=trunk_table_high_entries
        )


@dataclass
class GRPTBL_entry:
    """Deprecated"""
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
    memory_address: int

    @classmethod
    def parse(cls, grp_num, dataRange):
        return cls.parse_TRUNK_GROUP_entry(grp_num, dataRange.words, dataRange.start_address)

    @classmethod
    def parse_TRUNK_GROUP_entry(cls, grp_num, words, memory_address):
        mbr = words[0] & 2**8 > 0
        exists = words[0] & 2**7 > 0
        highest_member = words[0] & 0x7f
        sel_status_block_index = words[1] & 0x3fff
        member_list_index = words[2] & 0x3fff
        circuit_code = words[3] & 0x1f
        memory_address = memory_address
        return cls(grp_num, mbr, exists, highest_member, sel_status_block_index, member_list_index,
                   circuit_code, memory_address)

@dataclass
class SERVICE_GROUP_entry:
    """Figure 12C"""
    grp_num: int
    mbr: bool
    exists: bool
    highest_member: int
    sel_status_block_index: int
    member_list_index: int
    circuit_code: int
    memory_address: int

    @classmethod
    def parse(cls, grp_num, range):
        return cls.parse_SERVICE_GROUP_entry(grp_num, range.words, range.start_address)

    @classmethod
    def parse_SERVICE_GROUP_entry(cls, grp_num, words, memory_address):
        mbr = words[0] & 2**8 > 0
        exists = words[0] & 2**7 > 0
        highest_member = words[0] & 0x7f
        sel_status_block_index = words[1] & 0x3fff
        member_list_index = words[2] & 0x3fff
        circuit_code = words[3] & 0x1f
        memory_address = memory_address
        return cls(grp_num, mbr, exists, highest_member, sel_status_block_index, member_list_index,
                   circuit_code, memory_address)

@dataclass
class TRUNK_CIRCUIT_MEMBER_LIST_entry:
    spn: int
    ckt_code: int
    dta: int

    @classmethod
    def parse_TRUNK_GROUP_entry(cls, words):
        spn = words[0] & 0x1fff
        ckt_code = words[1] >> 11
        dta = words[1] & 0x7ff
        return cls(spn, ckt_code, dta)


def twentybit(a, b):
    """
    Convert two words into a single 20-bit integer.
    """
    return ((a & 0xf) << 16) + b

def load_track(base_filename, start_block=0, end_block=358):

    data_ranges = []

    for block_n in range(start_block, end_block):
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
                                  words=block_data[next_header+2:next_header+length])
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
                          words=np.copy(original_range.words[offset:]))
    return new_range

def print_data(target_address, block, length=5):
    offset = target_address - block.start_address
    if(offset < 0 or offset > (block.end_address - block.start_address)):
       raise ValueError("Target address not found in block")

    for n in range(offset, offset+length):
       print("{:06o}".format(block.words[n]))

def decode_scanpoint(scanpoint_field):
    """
    Translate a packed scanpoint into (scanner, row, entry) tuples.
    """
    return (scanpoint_field >> 9, (scanpoint_field >> 4) & 0b11111, scanpoint_field & 0b1111)

def decode_dta(value):
    """
    Decode a Distributor Triplet Address
    """
    return (value & 0xff, (value >> 8) & 0b11)

if __name__ == '__main__':



    base_filename = "TapeData/1/"
    data = load_track(base_filename)

    #MTI_base = 0o420000
    # MTI = 0o421410
    grptable_base = 0o421410

    # MTI_entries = [("GRPTBL", 0o421410)]

    grptable_data = range_starting_at_address(grptable_base, data)


    # grptbl_entry_pbx = GRPTBL_entry.parse_GRPTBL_entry(grptable_data.words)
    # grptbl_entry_svc = GRPTBL_entry.parse_GRPTBL_entry(grptable_data.words[3:])
    # grptbl_entry_trunks_low = GRPTBL_entry.parse_GRPTBL_entry(grptable_data.words[6:])
    # grptbl_entry_trunks_high = GRPTBL_entry.parse_GRPTBL_entry(grptable_data.words[9:])
    print("PBX/MLHG ", grptbl_entry_pbx)
    print("SVC CKTS ", grptbl_entry_svc)
    print("TRUNK GROUPS 128-191 ", grptbl_entry_trunks_low)
    print("TRUNK GROUPS 192-255 ", grptbl_entry_trunks_high)

    memlist_base = 0o421424

    memlist_data = range_starting_at_address(memlist_base, data)

    memlist_entry_pbx = GRPTBL_entry.parse_GRPTBL_entry(memlist_data.words)
    memlist_entry_svc = GRPTBL_entry.parse_GRPTBL_entry(memlist_data.words[3:])
    memlist_entry_trunks_low = GRPTBL_entry.parse_GRPTBL_entry(memlist_data.words[6:])
    memlist_entry_trunks_high = GRPTBL_entry.parse_GRPTBL_entry(memlist_data.words[9:])
    print("MEMLIST PBX/MLHG", memlist_entry_pbx)
    print("MEMLIST SVC CKTS", memlist_entry_svc)
    print("MEMLIST TRUNKS 128-191", memlist_entry_trunks_low)
    print("MEMLIST TRUNKS 192-255", memlist_entry_trunks_high)

    # groups = {}
    # for n in range(0, grptbl_entry_trunks_low.n_entries):
    #     group_number = 128 + n
    #     pointer = grptbl_entry_trunks_low.pointer + (8*n)
    #     trunk_data_range = range_starting_at_address(pointer, data)
    #     group_entry = TRUNK_GROUP_entry.parse_TRUNK_GROUP_entry(group_number,
    #                                                             trunk_data_range.words, pointer)
    #     groups[group_number] = group_entry

    # svc_groups = {}
    # for n in range(0, grptbl_entry_svc.n_entries):
    #     group_number = 64 + n
    #     pointer = grptbl_entry_svc.pointer + (4*n)
    #     svc_data_range = range_starting_at_address(pointer, data)
    #     group_entry = SERVICE_GROUP_entry.parse_SERVICE_GROUP_entry(group_number,
    #                                                                 svc_data_range.words, pointer)
    #     svc_groups[group_number] = group_entry

    if False:
        print("Service Circuits:")
        for group_n, group in svc_groups.items():
            if(group.exists):
                print(group)

        print("Trunks:")
        for group_n, group in groups.items():
            if(group.exists):
                print(group)

    print("-"*20)

    print("Service Circuits:")
    svc_table_head = range_starting_at_address(memlist_entry_svc.pointer, data)
    print("Format {:02b} N members: {:d}, N spares: {:d}".format((svc_table_head.words[0] >> 14) & 0b11,
                                                                 (svc_table_head.words[0] >> 7) & 0x7f,
                                                                 svc_table_head.words[0] & 0x7f))



    for group_n, svc_group in svc_groups.items():

        if(not svc_group.exists):
            continue
        member_list_range = range_starting_at_address(memlist_entry_svc.pointer +
                                                      svc_group.member_list_index, data)
        print("GROUP {:3d} N members: {:d}, N spares: {:d}".format(group_n,
                                                                   (member_list_range.words[0] >> 7) & 0x7f,
                                                                   member_list_range.words[0] & 0x7f))
        print(f"Start address: 0o{member_list_range.start_address:o}, End address: 0o{member_list_range.end_address:o}")
        print(f"Header byte: 0o{member_list_range.words[0]:o}")

        group_format = member_list_range.words[0] >> 14

        for member_n in range(0, svc_group.highest_member + 1):
            offset = memlist_entry_svc.pointer + svc_group.member_list_index + member_n//2 + 1

            svc_data = range_starting_at_address(offset, data)
            if(member_n % 2 == 1):
                svcnbr = svc_data.words[0] >> 8
            else:
                svcnbr = svc_data.words[0] & 0xff

            if group_format == 0:
                print("Group {:d} Member {:d} PBX Hunt addr {:o}".format(group_n, member_n, offset))

            elif group_format == 2:

                high_offset = memlist_entry_svc.pointer + svc_group.member_list_index + math.ceil((svc_group.highest_member + 1)/2) + member_n + 1
                svc_data_high = range_starting_at_address(high_offset, data)
                ckt_code = svc_data_high.words[0] >> 11
                dta = svc_data_high.words[0] & 0xfff
                dp_PD, dp_trip = decode_dta(dta)

                scanpoint_string = "{:02d} {:02d} {:02d}".format(*decode_scanpoint(svcnbr))
                print("Group {:d} Member {:d} SVCNBR {:s}, ckt_code {:d}, DP {:03d} {:d} ({:d}) addr {:o}".format(group_n,
                                                                                                                  member_n,
                                                                                                                  scanpoint_string,
                                                                                                                  ckt_code,
                                                                                                                  dp_PD,
                                                                                                                  dp_trip,
                                                                                                                  dta,
                                                                                                                  offset))
            elif group_format == 1:
                TEN = member_list_range.words[member_n + 1]
                print("Group {:d} Member {:d} TEN {:04o} addr {:o}".format(group_n,
                                                                           member_n,
                                                                           TEN,
                                                                           offset))
            else:
                print("Group {:d} Member {:d} unknown format addr {:o}".format(group_n,
                                                                               member_n,
                                                                               offset))



    print("-"*20)
    print("Trunks:")

    for group_n, trunk_group in groups.items():
        member_list_range = range_starting_at_address(memlist_entry_trunks_low.pointer +
                                                      trunk_group.member_list_index, data)
        if(trunk_group.exists == False):
            continue
        print("GROUP {:3d} N members: {:d}, N spares: {:d}".format(group_n,
                                                                   (member_list_range.words[0] >> 7) & 0x7f,
                                                                   member_list_range.words[0] & 0x7f))
        for member_n in range(0, trunk_group.highest_member + 1):

            circuit_member_pointer = memlist_entry_trunks_low.pointer + trunk_group.member_list_index + member_n*2 + 1
            circuit_member = range_starting_at_address(circuit_member_pointer, data)
            # SPN = Scan Point Number
            # DTA = distributor triplet address
            scanpoint_field = circuit_member.words[0] & 0x1fff
            scanpoint_string = "{:02d} {:02d} {:02d}".format(*decode_scanpoint(scanpoint_field))
            distribute_field = circuit_member.words[0] & 0x1fff
            distribute_string = "{:01d} {:03d} {:01d}".format(distribute_field >> 11,
                                                             (distribute_field >> 2) & 0x1ff,
                                                             distribute_field & 0b11)

            cktcode = circuit_member.words[1] >> 11
            print(f"GROUP {group_n:d}, MEMBER {member_n:d}, SPN {scanpoint_string:s}, "
                  f"DTA {distribute_string:s} ({distribute_field:d}), CKTCODE {cktcode:d} ")

