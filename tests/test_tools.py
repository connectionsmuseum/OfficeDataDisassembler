
import numpy as np
from officedata.image_tools import DataRange, DataRangeSet


def test_merge_ranges():

    range_set = DataRangeSet([DataRange(100, (33 + np.zeros(10, dtype=np.uint16)).astype(np.uint16)),
                              DataRange(110, np.array([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14]).astype(np.uint16))])
    new_range = range_set.range_starting_at_address(105, 10)
    assert sum(new_range.words == 33) == 5
    assert new_range.start_address == 105
    assert len(new_range.words) == 10
    assert new_range.words[6] == 1

    new_range = range_set.range_starting_at_address(115, 5)
    assert new_range.start_address == 115
    assert new_range.words[0] == 5

    assert new_range.subset(3, 2).words[0] == 8

def test_merge_three_ranges():

    range_set = DataRangeSet([DataRange(100, (1 + np.zeros(10, dtype=np.uint16)).astype(np.uint16)),
                              DataRange(110, (2 + np.zeros(10)).astype(np.uint16)),
                              DataRange(120, (3 + np.zeros(10)).astype(np.uint16))])
    new_range = range_set.range_starting_at_address(105, 25)
    assert sum(new_range.words == 1) == 5
    assert sum(new_range.words == 2) == 10 
    assert sum(new_range.words == 3) == 10
    assert len(new_range.words) == 25

def test_no_merge_ranges():
    """If no length is specified, only the remainder of the single range is returned."""

    range_set = DataRangeSet([DataRange(100, (1 + np.zeros(10, dtype=np.uint16)).astype(np.uint16)),
                              DataRange(110, (2 + np.zeros(10)).astype(np.uint16))])
    new_range = range_set.range_starting_at_address(105)
    assert sum(new_range.words == 1) == 5
    assert sum(new_range.words == 2) == 0

def test_address():
    """If no length is specified, only the remainder of the single range is returned."""

    data_range = DataRange(100, np.array([1,2,3,4,5,6,7,8,9,10]).astype(np.uint16))
    new_range = data_range.subset(0, 3)
    assert new_range.start_address == 100

    new_range = data_range.subset(2, 3)
    assert new_range.start_address == 102
    assert new_range.words[0] == 3

    new_range = data_range.subset_at_address(104, 3)
    assert new_range.start_address == 104
    assert new_range.words[0] == 5
