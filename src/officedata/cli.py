
from typing import Annotated
import typer

from .image_tools import load_track
from .odd import GRPTBL, MEMLST, MEMLST_SVC_GROUP, SPTBL
from .display import display_svc_circuits

main = typer.Typer()

@main.command()
def scanpoints(
    oe: Annotated[str | None, typer.Option(help="Six octal digit OE number")] = None,
    ten: Annotated[str | None, typer.Option(help="Six octal digit TEN number")] = None,
):
    """Lookup entries in the scan point table (Figure 2.)"""

    # Eventually assert that one of several possible address formats is provided.
    if oe is None and ten is None:
        raise typer.BadParameter("Either OE or TEN must be specified")

    if oe and len(oe) != 6:
        raise typer.BadParameter("OE must be six octal digits")

    if ten and len(ten) != 6:
        raise typer.BadParameter("TEN must be six octal digits")

    if oe:
        try:
            int(oe, base=8)
        except ValueError:
            raise typer.BadParameter("OE must be six octal digits")

    if ten:
        try:
            int(ten, base=8)
        except ValueError:
            raise typer.BadParameter("TEN must be six octal digits")

    base_filename = "TapeData/1/"
    data = load_track(base_filename, start_block=167, end_block=317)

    SPTBL_base = 0o421443
    sptbl = SPTBL.find(SPTBL_base, data)

    if oe:
        print(sptbl.spn_head.lookup_oe(oe))
    elif ten:
        print(sptbl.spn_head.lookup_oe(ten))

@main.command()
def grptable(group_number: int):
    """Look up a service circuit group in the member list table (Figure 15.)"""

    base_filename = "TapeData/1/"
    data = load_track(base_filename, start_block=167, end_block=317)

    MEMLST_base = 0o421424
    memlist = MEMLST.parse(data.range_starting_at_address(MEMLST_base))

    grptable_base = 0o421410

    grptbl = GRPTBL.parse(grptable_base, data)

    for entry in grptbl.svc_table.groups:
        if entry.grp_num != group_number:
            continue
        print(entry)

        # TODO: Move this out of the CLI handling code.
        memlist_grp: MEMLST_SVC_GROUP = MEMLST_SVC_GROUP.parse(entry.highest_member,
                                    data.range_starting_at_address(memlist.memlist_svc.member_list_address + entry.member_list_index))

        print(memlist_grp)
        for memlist_entry in memlist_grp.members:
            print(memlist_entry)

@main.command()
def blocks():

    base_filename = "TapeData/1/"

    for block_n in range(167, 317):
        data = load_track(base_filename, start_block=block_n, end_block=block_n + 1)
        if data and len(data.ranges) > 0:
            print(f"Block {block_n}: 0o{data.ranges[0].start_address:o} - 0o{data.ranges[0].start_address + data.ranges[0].length:o} ")
        else:
            print(f"Block {block_n} no data")


