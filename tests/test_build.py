"""Test building the office data tree from the disk image"""

from officedata.odd import load_track, GRPTBL


def test_build_tree():

    base_filename = "TapeData/1/"
    data = load_track(base_filename)

    grptable_base = 0o421410

    grptbl = GRPTBL.parse(grptable_base, data)

    assert grptbl.svc_table.group_count > 5
    assert len(grptbl.svc_table.groups) > 5

