

from .image_tools import load_track
from .odd import GRPTBL, MEMLST, MEMLST_SVC_GROUP
from .display import display_svc_circuits

def main():

    base_filename = "TapeData/1/"
    data = load_track(base_filename)

    #MTI_base = 0o420000

    #MEMLST_base = 0o421410
    MEMLST_base = 0o421424
    memlist = MEMLST.parse(data.range_starting_at_address(MEMLST_base))

    grptable_base = 0o421410

    grptbl = GRPTBL.parse(grptable_base, data)


    print(memlist.memlist_svc)
    print(memlist.memlist_trunks_high)
    print(memlist.memlist_trunks_low)
    #for entry in grptbl.svc_table.groups:
    #    print(entry)

    for entry in grptbl.svc_table.groups:
        if entry.grp_num != 64:
            continue
        print(entry)

        memlist_grp = MEMLST_SVC_GROUP.parse(entry.highest_member,
                                             data.range_starting_at_address(memlist.memlist_svc.member_list_address + 2*entry.member_list_index))
        print(memlist_grp)

    # print(memlist.memlist_svc.by_index(58))


    #display_svc_circuits(grptbl.svc_table_entries)


