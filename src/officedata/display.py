""""Functions to create useful displays of the office data tree"""


from .odd import SERVICE_GROUP_entry, SERVICE_GROUP_TABLE
from .image_tools import decode_scanpoint, decode_dta


def display_svc_circuits(svc_table: SERVICE_GROUP_TABLE):

    for group_n, svc_group in enumerate(svc_table.entries):
        pass

        #entry_address = svc_table.table_address + svc_group.member_list_index + group_n//2 + 1
        #svc_data = svc_table.range.subset_at_address(entry_address, )

def __display_svc_circuits(svc_entries):

    for group_n, svc_group in svc_entries.items():

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

def display_trunk_entries(trunk_entries):

    for group_n, trunk_group in trunk_entries.items():
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