
from dataclasses import dataclass

from .image_tools import twentybit, load_track, DataRange, DataRangeSet, decode_dta

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
        if len(words) < 4:
            raise ValueError(f"TRUNK_GROUP_entry requires 4 words; only {len(words):d} provided.")
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
    """Individual entry on Figure 12C"""
    grp_num: int
    mbr: bool
    exists: bool
    highest_member: int
    sel_status_block_index: int
    member_list_index: int
    circuit_code: int
    memory_address: int
    data: DataRange

    @classmethod
    def parse(cls, grp_num, data):
        return cls.parse_SERVICE_GROUP_entry(grp_num, data.words, data.start_address, data)

    @classmethod
    def parse_SERVICE_GROUP_entry(cls, grp_num, words, memory_address, data):
        if len(data.words) < 4:
            raise ValueError(f"SERVICE_GROUP_entry requires 4 words; only {len(data.words):d} provided.")
        mbr = words[0] & 2**8 > 0
        exists = words[0] & 2**7 > 0
        highest_member = words[0] & 0x7f
        sel_status_block_index = words[1] & 0x3fff
        member_list_index = words[2] & 0x3fff
        circuit_code = words[3] & 0x1f
        memory_address = memory_address
        return cls(grp_num, mbr, exists, int(highest_member), int(sel_status_block_index), int(member_list_index),
                   int(circuit_code), int(memory_address), data=data)
@dataclass
class SERVICE_GROUP_TABLE:
    """Figure 12C table"""

    range: DataRange
    table_address: int
    group_count: int
    groups: list[SERVICE_GROUP_entry]

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

@dataclass
class SERVICE_GROUP:

    group_n: int
    n_members: int
    n_spares: int
    format: int
    members: list[SERVICE_GROUP_entry]
    data: DataRange

    @classmethod
    def parse(cls, group_n: int, data: DataRange):
        n_members = (data.words[0] >> 7) & 0x7f
        n_spares = data.words[0] & 0x7f
        group_format = data.words[0] >> 14
        entries = []
        for member_index in range(0, n_members + n_spares):
            member_address = data.start_address + member_index//2 + 1
            entry = SERVICE_GROUP_entry.parse(group_n, data.subset_at_address(member_address, 4))
            entries.append(entry)
        return cls(group_n, n_members, n_spares, group_format, entries, data)

    def __str__(self):
        return f"GROUP {self.group_n:3d} N members: {self.n_members:d}, N spares: {self.n_spares:d}, format: {self.format:d}"

    def print_extended(self):
        print(str(self))
        print(f"Start address: 0o{self.data.start_address:o}, End address: 0o{self.data.end_address:o}")
        print(f"Header byte: 0o{self.data.words[0]:o}")


@dataclass
class GRPTBL:
    range_set: DataRangeSet
    pbx_table_address: int
    pbx_table_entry_count: int
    pbx_table_entries: list   #unused

    svc_table: SERVICE_GROUP_TABLE

    trunk_table_low_address: int
    trunk_table_low_entry_count: int
    trunk_table_low_entries: list[TRUNK_GROUP_entry]

    trunk_table_high_address: int
    trunk_table_high_entry_count: int
    trunk_table_high_entries: list[TRUNK_GROUP_entry]

    @classmethod
    def parse(cls, grptbl_address, range_set: DataRangeSet):
        """Parse the GRPTBL.
        This contains pointers to tables that could be in other areas of memory, so a DataRangeSet is required.
        """

        # grptbl_entry_pbx = GRPTBL_entry.parse_GRPTBL_entry(grptable_data.words)
        # grptbl_entry_svc = GRPTBL_entry.parse_GRPTBL_entry(grptable_data.words[3:])
        # grptbl_entry_trunks_low = GRPTBL_entry.parse_GRPTBL_entry(grptable_data.words[6:])
        # grptbl_entry_trunks_high = GRPTBL_entry.parse_GRPTBL_entry(grptable_data.words[9:])

        def parse_entry(dataRange):
            n_entries = dataRange.words[1] >> 4
            pointer = twentybit(dataRange.words[1], dataRange.words[2])
            return pointer, n_entries

        # svc_table_address, svc_table_entry_count = parse_entry(dataRange.subset(3,3))
        # trunk_table_low_address, trunk_table_low_entry_count = parse_entry(dataRange.subset(6,3))
        # trunk_table_high_address, trunk_table_high_entry_count = parse_entry(dataRange.subset(9,3))
        # print(f"{svc_table_address:o}, {trunk_table_low_address:o}, {trunk_table_high_address:o}")

        table_range = range_set.range_starting_at_address(grptbl_address)

        svc_table_address, svc_table_entry_count = parse_entry(table_range.subset(3,3))
        svc_table_groups = []
        for n in range(0, svc_table_entry_count):
            group_number = 64 + n
            pointer = svc_table_address + (4*n)
            svc_data_range = range_set.range_starting_at_address(pointer, 4)
            # print(f"{pointer:o}, {svc_data_range.end_address:o}")
            group = SERVICE_GROUP_entry.parse(group_number, svc_data_range)
            svc_table_groups.append(group)

        svc_table = SERVICE_GROUP_TABLE(range=range_set.range_starting_at_address(svc_table_address),
                                        table_address=svc_table_address,
                                        group_count=svc_table_entry_count,
                                        groups=svc_table_groups)

        trunk_table_low_address, trunk_table_low_entry_count = parse_entry(table_range.subset(6,3))
        trunk_table_low_entries = []
        for n in range(0, trunk_table_low_entry_count):
            group_number = 128 + n
            pointer = trunk_table_low_address + (8*n)
            trunk_data_range = range_set.range_starting_at_address(pointer, 8)
            group_entry = TRUNK_GROUP_entry.parse(group_number, trunk_data_range)
            trunk_table_low_entries.append(group_entry)

        trunk_table_high_address, trunk_table_high_entry_count = parse_entry(table_range.subset(9,3))
        trunk_table_high_entries = []
        for n in range(0, trunk_table_high_entry_count):
            group_number = 128 + n
            pointer = trunk_table_high_address + (8*n)
            trunk_data_range = range_set.range_starting_at_address(pointer, 8)
            group_entry = TRUNK_GROUP_entry.parse(group_number, trunk_data_range)
            trunk_table_high_entries.append(group_entry)

        return cls(range_set=range_set,
                   pbx_table_address=0,
                   pbx_table_entry_count=0,
                   pbx_table_entries=[],
                   svc_table=svc_table,
                   trunk_table_low_address=trunk_table_low_address,
                   trunk_table_low_entry_count=trunk_table_low_entry_count,
                   trunk_table_low_entries=trunk_table_low_entries,
                   trunk_table_high_address=trunk_table_high_address,
                   trunk_table_high_entry_count=trunk_table_high_entry_count,
                   trunk_table_high_entries=trunk_table_high_entries
        )


@dataclass
class MASTER_TABLE_INDEX:
    """These are mostly fixed values"""
    pass


@dataclass
class MEMLIST_SVC_MEMBER:
    """Individual entry on Figure 15C"""
    scanpoint: int
    cktcode: int
    dta: int

    def __repr__(self):
        return f"MEMLIST_SVC_MEMBER(scanpoint={self.scanpoint:d}, cktcode={self.cktcode:d}, dta={decode_dta(self.dta)}"

@dataclass
class MEMLST_SVC_GROUP:
    """Figure 15C"""
    n_members: int
    n_spares: int
    group_format: int

    members: list[MEMLIST_SVC_MEMBER]

    @classmethod
    def parse(cls, highest_mem: int, data: DataRange):
        n_members = (data.words[0] >> 7) & 0x7f
        n_spares = data.words[0] & 0x7f
        group_format = data.words[0] >> 14

        members = []
        for n in range(0, n_members):
            scanpoint = data.words[n//2 + 1] & 0xff if n % 2 == 0 else data.words[n//2 + 1] >> 8
            dta = data.words[n + 1 + (highest_mem + 1)//2] & 0x7ff
            cktcode = data.words[n + 1 + (highest_mem + 1)//2] >> 11
            members.append(MEMLIST_SVC_MEMBER(scanpoint=scanpoint, dta=dta, cktcode=cktcode))

        return cls(n_members=n_members, n_spares=n_spares, group_format=group_format, members=members)


@dataclass
class MEMLST_entry:
    """Figure 15A"""
    header: int
    member_list_words_minus_one: int
    member_list_address: int
    data: DataRange

    @classmethod
    def parse(cls, dataRange):
        header = dataRange.words[0]
        max_words = dataRange.words[1] >> 4
        address = twentybit(dataRange.words[1], dataRange.words[2])
        return cls(header=header, member_list_words_minus_one=max_words, member_list_address=address, data=dataRange)

@dataclass
class MEMLST:
    """Figure 15. The Member List is contains individual trunk and service
    circuit member data, pointed to by the group lists. """
    memlist_pbx: MEMLST_entry
    memlist_svc: MEMLST_entry
    memlist_trunks_low: MEMLST_entry
    memlist_trunks_high: MEMLST_entry

    @classmethod
    def parse(cls, data: DataRange):
        memlist_pbx = MEMLST_entry.parse(data.subset(0,3))
        memlist_svc = MEMLST_entry.parse(data.subset(3,3))
        memlist_trunks_low = MEMLST_entry.parse(data.subset(6,3))
        memlist_trunks_high = MEMLST_entry.parse(data.subset(9,3))

        return cls(memlist_pbx=memlist_pbx,
                   memlist_svc=memlist_svc,
                   memlist_trunks_low=memlist_trunks_low,
                   memlist_trunks_high=memlist_trunks_high)


def cli():
    """Deprecated, should be handled in cli.py"""

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


