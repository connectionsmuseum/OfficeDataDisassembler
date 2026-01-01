
import numpy as np
from officedata.image_tools import DataRange, DataRangeSet


def test_merge_ranges():

    range_set = DataRangeSet([DataRange(100, 110, (1 + np.zeros(10, dtype=np.uint16)).astype(np.uint16)),
                              DataRange(110, 125, (2 + np.zeros(15)).astype(np.uint16))])
    new_range = range_set.range_starting_at_address(105, 10)
    assert sum(new_range.words == 1) == 5
    assert sum(new_range.words == 2) == 5
    assert new_range.start_address == 105
    assert len(new_range.words) == 10

def test_merge_three_ranges():

    range_set = DataRangeSet([DataRange(100, 110, (1 + np.zeros(10, dtype=np.uint16)).astype(np.uint16)),
                              DataRange(110, 125, (2 + np.zeros(15)).astype(np.uint16)),
                              DataRange(120, 130, (3 + np.zeros(10)).astype(np.uint16))])
    new_range = range_set.range_starting_at_address(105, 25)
    assert sum(new_range.words == 1) == 5
    assert sum(new_range.words == 2) == 15
    assert sum(new_range.words == 3) == 5
    assert len(new_range.words) == 25

def test_no_merge_ranges():
    """If no length is specified, only the remainder of the single range is returned."""

    range_set = DataRangeSet([DataRange(100, 110, (1 + np.zeros(10, dtype=np.uint16)).astype(np.uint16)),
                              DataRange(110, 120, (2 + np.zeros(10)).astype(np.uint16))])
    new_range = range_set.range_starting_at_address(105)
    assert sum(new_range.words == 1) == 5
    assert sum(new_range.words == 2) == 0

