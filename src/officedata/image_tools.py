
import numpy as np
import numpy.typing as npt
import os
import struct
from dataclasses import dataclass

@dataclass
class DataRange:
    start_address: int
    end_address: int
    words: npt.NDArray[np.uint16]

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

    def __repr__(self):
        return f"DataRange(start_address=0o{self.start_address:o}, end_address=0o{self.end_address:o})"


class DataRangeSet:
    """
    A DataRangeSet contains multiple ranges which need not be contiguous. This
    is equivalent to the set of blocks in a track of the tape.
    """

    ranges: list[DataRange]

    def __init__(self, ranges: list[DataRange]):
        self.ranges = ranges

    def _find_range(self, target_address: int) -> DataRange:
        """Find a range and return it verbatim."""
        for data_range in self.ranges:
            if((target_address >= data_range.start_address) and
            (target_address < data_range.end_address)):
                return data_range

        raise ValueError("Target address not found in data")

    def range_starting_at_address(self, target_address: int, length: int = 0) -> DataRange:
        """
        Return a range starting at the target address.

        Range is truncated to `length` if specified, otherwise the remainder of
        the DataRange is returned.
        """

        original_range = self._find_range(target_address)
        offset = target_address - original_range.start_address
        new_range = DataRange(start_address=original_range.start_address + offset,
                            end_address=original_range.end_address,
                            words=np.copy(original_range.words[offset:(offset+length)] if length > 0
                                          else original_range.words[offset:]))
        return new_range


def twentybit(a, b):
    """
    Convert two words into a single 20-bit integer.
    """
    return ((a & 0xf) << 16) + b

def load_track(base_filename, start_block=0, end_block=358) -> DataRangeSet:

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

    return DataRangeSet(data_ranges)


def load_block(filename: str):
    f = open(filename, "rb")

    read_len = 50
    words = []
    while True:
        data = f.read(2*read_len)
        if(len(data) == 0):
            break
        successful_len = len(data)//2

        new_words = struct.unpack(f'>{successful_len}H', data)

        words.extend(new_words)
    return np.array(words)

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