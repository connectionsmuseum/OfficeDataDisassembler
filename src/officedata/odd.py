
from dataclasses import dataclass

from .image_tools import twentybit, load_track, DataRange, DataRangeSet, decode_dta, decode_scanpoint

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

    def __repr__(self):
        return (f"SERVICE_GROUP_entry(grp_num={self.grp_num}, mbr={self.mbr}, exists={self.exists}, highest_member={self.highest_member}, "
                f"circuit_code={self.circuit_code:d} address={self.data.start_address:o} word0=0o{self.data.words[0]:o})")


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
        print(f"Start address: 0o{self.data.start_address:o}, End address: 0o{(self.data.start_address + self.data.length):o}")
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
    scanpoint: int = 0
    cktcode: int = 0
    dta: int = 0
    ten: int = 0

    def __repr__(self):
        return f"MEMLIST_SVC_MEMBER(scanpoint={self.scanpoint:d}, cktcode={self.cktcode:d}, dta={decode_dta(self.dta)}, ten=0o{self.ten:o})"

@dataclass
class MEMLST_SVC_GROUP:
    """Figure 15C"""
    n_members: int
    n_spares: int
    group_format: int
    address: int

    members: list[MEMLIST_SVC_MEMBER]

    @classmethod
    def parse(cls, highest_mem: int, data: DataRange):
        n_members = (data.words[0] >> 7) & 0x7f
        n_spares = data.words[0] & 0x7f
        group_format = data.words[0] >> 14

        members = []

        if group_format == 1:
            for n in range(0, n_members):
                ten = data.words[n + 1] & 0xfff
                members.append(MEMLIST_SVC_MEMBER(ten=ten))

        elif group_format == 2:
            for n in range(0, n_members):
                scanpoint = data.words[n//2 + 1] & 0xff if n % 2 == 0 else data.words[n//2 + 1] >> 8
                dta = data.words[n + 1 + (highest_mem + 1)//2] & 0x7ff
                cktcode = data.words[n + 1 + (highest_mem + 1)//2] >> 11
                members.append(MEMLIST_SVC_MEMBER(scanpoint=scanpoint, dta=dta, cktcode=cktcode))

        return cls(n_members=n_members, n_spares=n_spares, group_format=group_format, members=members, address=data.start_address)

    def __repr__(self):
        return (f"MEMLST_SVC_GROUP(n_members={self.n_members:d}, n_spares={self.n_spares:d}, "
                f"group_format={self.group_format:d}, address=0o{self.address:o} members=[{len(self.members)} entries])")


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

@dataclass
class UNIV_SUBTRANSLATOR:
    address: int
    u_type: int
    ten: int | None = None
    mem_number: int | None = None
    grp_number: int | None = None
    tone_scanpoint: int | None = None
    supv_scanpoint: int | None = None
    n_lines: int | None = None

    @classmethod
    def parse(cls, data: DataRange):
        address = data.start_address
        u_type = data.words[0] >> 13

        match u_type:
            case 1 | 2:
                ten = data.words[0] & 0x1ff
                grp_number = data.words[1] & 0xff
                mem_number = data.words[1] >> 8
                return cls(address=address, u_type=u_type, ten=ten, grp_number=grp_number, mem_number=mem_number)

            case 3:
                tone_scanpoint = data.words[0] & 0x1ff
                return cls(address=address, u_type=u_type, tone_scanpoint=tone_scanpoint)

            case 4:
                supv_scanpoint = data.words[0] & 0x1ff
                return cls(address=address, u_type=u_type, supv_scanpoint=supv_scanpoint)

            case _:
                return cls(address=address, u_type=u_type)

@dataclass
class LINE_SUBTRANSLATOR:
    address: int
    u_type: int
    data: DataRange
    terminal: int | None = None
    group: int | None = None
    scanpoint: tuple[int, int, int] | None = None

    @classmethod
    def parse(cls, data: DataRange):
        address = data.start_address
        u_type = data.words[0] >> 12

        match u_type:
            case 10:
                scanpoint = data.words[1] & 0xfff
                return cls(address=address, u_type=u_type, data=data, scanpoint=decode_scanpoint(scanpoint))

            case 11:
                terminal = data.words[1] >> 8
                group = data.words[1] & 0xff
                return cls(address=address, u_type=u_type, data=data, terminal=terminal, group=group)

            case _:
                return cls(address=address, u_type=u_type, data=data)

    def __repr__(self):
        if self.terminal and self.group:
            return (f"LINE_SUBTRANSLATOR(address=0o{self.address:o}, u_type={self.u_type:d}, terminal={self.terminal:d}, "
                f"group={self.group:d}, scanpoint={self.scanpoint}, data=[0o{self.data.words[0]:o}, 0o{self.data.words[1]:o}]")
        else:
            return (f"LINE_SUBTRANSLATOR(address=0o{self.address:o}, u_type={self.u_type:d}, terminal={self.terminal}, "
                f"group={self.group}, scanpoint={self.scanpoint}, data=[0o{self.data.words[0]:o}, 0o{self.data.words[1]:o}]")

@dataclass
class SPN_HEAD_TABLE:
    data: DataRangeSet
    table_address: int

    def lookup_scanpoint(self, scanner: int, row: int, col: int):
        w_index = (scanner << 3) | (row >> 2)
        x_index = ((row & 0b11) << 4) | col
        return self._lookup_entry(w_index, x_index)

    def lookup_oe(self, oe: str) -> LINE_SUBTRANSLATOR | UNIV_SUBTRANSLATOR:
        """This OE is the concatenated string,
         [2 digit Concentrator Group][Concentrator][Switch Group][Switch][Level]
         Where all the other fields are one octal digit.

        E.g.: 010016 is CG 1, Switch 1, Level 6.
        """

        oe_int = self._oe_string_to_number(oe)

        # XXX: This minus one offset isn't documented.
        return self._lookup_entry(oe_int >> 6, (oe_int & 0x3f) - 0)

    def lookup_ten(self, ten: str) -> LINE_SUBTRANSLATOR | UNIV_SUBTRANSLATOR:

        ten_int = self._ten_string_to_number(ten)
        return self._lookup_entry(ten_int >>6, (ten_int & 0x3f) - 0)

    @staticmethod
    def _oe_string_to_number(oe: str) -> int:
        if len(oe) != 6:
            raise ValueError("OE must be a six digit string")
        cg = int(oe[0:2], base=8)
        c = int(oe[2], base=8)
        sg = int(oe[3], base=8)
        sw = int(oe[4], base=8)
        lv = int(oe[5], base=8)
        return (cg << 9) | (c << 8) | (sg << 6) | (sw << 3) | lv

    @staticmethod
    def _ten_string_to_number(ten: str) -> int:
        if len(ten) != 6:
            raise ValueError("OE must be a six digit string")
        cg = int(ten[0:2], base=8)
        c = int(ten[2], base=8)
        sg = int(ten[3], base=8)
        sw = int(ten[4], base=8)
        lv = int(ten[5], base=8)
        return (cg << 9) | (sg << 7) | (c << 6) | (sw << 3) | lv

    def _lookup_entry(self, w_index: int, x_index: int) -> LINE_SUBTRANSLATOR | UNIV_SUBTRANSLATOR:
        """
        Misc subtranslator is indexed differently from Line and Univeral subtranslators"""

        entry = self.data.range_starting_at_address(self.table_address, 127).words[w_index]

        store_increment = entry & 0x3ff
        sub_type = entry >> 14

        if sub_type == 1:
            # Misc subtranslator
            subtranslator_entry = self.data.range_starting_at_address(self.table_address + w_index + store_increment + x_index, 1)
        else:
            subtranslator_entry = self.data.range_starting_at_address(self.table_address + w_index + store_increment + 2*x_index, 2)

        match sub_type:
            case 0:
                raise ValueError(f"Unassigned subtranslator type {sub_type}")
            case 1:
                raise NotImplementedError("Miscelaneous subtranslator not implemented")
            case 2:
                return UNIV_SUBTRANSLATOR.parse(subtranslator_entry)
            case 3:
                return LINE_SUBTRANSLATOR.parse(subtranslator_entry)
            case _:
                raise ValueError(f"Unknown subtranslator type {sub_type}")

@dataclass
class SPTBL:
    """Figure 2. Scan point number translator.
    Decodes a scan point into data on Figures 2A, 2B, 2C.
    """
    n_entries: int
    spn_head_table_address: int
    spn_head: SPN_HEAD_TABLE

    @classmethod
    def find(cls, base_address, all_data: DataRangeSet):
        """Find the table in the set of tape blocks and load the spn_head table with data."""
        table_data = all_data.range_starting_at_address(base_address, 3)
        n_entries = table_data.words[1] >> 4
        address = twentybit(table_data.words[1], table_data.words[2])

        spn_head = SPN_HEAD_TABLE(data=all_data, table_address=address)
        return cls(n_entries=n_entries, spn_head_table_address=address, spn_head=spn_head)

