#
# Copyright 2017 Hyperkernel Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import sys
import z3

import libirpy
from libirpy import util
from hv6py.base import BaseStruct, Struct, Map, Refcnt, Refcnt2

# inital ctx with metadata, then find all of enum, and initial page_type
# file_type proc_state and intremap_state.
def _populate_enums():
    module = sys.modules[__name__]
    ctx = libirpy.newctx()
    import hv6py.kernel.impl as hv6
    hv6._init_metadata(ctx)
    for k, v in ctx.metadata.items():
        if isinstance(v, tuple) and v[0] == 'DICompositeType':
            if v[1].get('tag') == 'DW_TAG_enumeration_type':
                name = v[1].get('name')
                size = v[1].get('size')
                elements = v[1].get('elements')

                if name is None or size is None or elements is None:
                    continue

                setattr(module, name + '_t', z3.BitVecSort(size))
                enum = {}
                # get the enum name and value
                for element in ctx.metadata.get(elements):
                    element = ctx.metadata.get(element)
                    assert element[0] == 'DIEnumerator'
                    element_name = element[1].get('name')
                    element_value = element[1].get('value')
                    enum[element_name] = z3.BitVecVal(element_value, size)
                setattr(module, name, type(name, (), enum))



# These are populated from llvm metadata info
page_type_t = None
file_type_t = None
proc_state_t = None
intremap_state_t = None


# Fetch the enums from the llvm metadata and populate this module with their values
_populate_enums()
# when I define following type use class directly, it not works.
assert page_type_t is not None
assert file_type_t is not None
assert proc_state_t is not None

PAGE_SIZE = 4096

PCI_START = 0xa0000000
PCI_END =   0x100000000
# page number 
NPAGE = 8192
NDMAPAGE = 512
NPROC = 64
# NTSLICE
# max opend file
NOFILE = 16
# max file number
NFILE = 128
# max device number
NPCIDEV = 64
# max intermap number, what is used for?
NINTREMAP = 8
# max PIC page number
NPCIPAGE = (PCI_END - PCI_START) / PAGE_SIZE

# use z3py type define c type.
bool_t = z3.BoolSort()

size_t = z3.BitVecSort(64)
uint64_t = z3.BitVecSort(64)
uint32_t = z3.BitVecSort(32)
uint16_t = z3.BitVecSort(16)
uint8_t = z3.BitVecSort(8)


ssize_t = z3.BitVecSort(64)
int64_t = z3.BitVecSort(64)
int32_t = z3.BitVecSort(32)
int16_t = z3.BitVecSort(16)
int8_t = z3.BitVecSort(8)
int = int32_t

#page number
pn_t = z3.BitVecSort(64)
# dma page number
dmapn_t = z3.BitVecSort(64)
# file number
fn_t = z3.BitVecSort(64)
# file descriptor
fd_t = z3.BitVecSort(32)
# page table entry
pte_t = z3.BitVecSort(64)
dmar_pte_t = z3.BitVecSort(64)
# process id
pid_t = z3.BitVecSort(64)
# ???
off_t = z3.BitVecSort(64)
# device id
devid_t = z3.BitVecSort(16)
# ????
uintptr_t = z3.BitVecSort(64)
# physicall address
physaddr_t = uintptr_t
# initial process id
INITPID = z3.BitVecVal(1, pid_t)

MAX_INT64 = z3.BitVecVal(2 ** 64 - 1, 64)

# 4 level page table 
def FreshVA():
    idx1 = util.FreshBitVec('idx1', size_t)
    idx2 = util.FreshBitVec('idx2', size_t)
    idx3 = util.FreshBitVec('idx3', size_t)
    idx4 = util.FreshBitVec('idx4', size_t)
    return [idx1, idx2, idx3, idx4]


def BIT64(bit): return z3.BitVecVal(1 << bit, 64)
def has_bit(v, bit): return (v & bit) != 0


PTE_P = BIT64(0)                            # present
PTE_W = BIT64(1)                            # writable
PTE_U = BIT64(2)                            # user
PTE_PWT = BIT64(3)                          # write through
PTE_PCD = BIT64(4)                          # cache disable
PTE_A = BIT64(5)                            # accessed
PTE_D = BIT64(6)                            # dirty
PTE_PS = BIT64(7)                           # page size
PTE_G = BIT64(8)                            # global
PTE_AVL = BIT64(9) | BIT64(10) | BIT64(11)  # available for software use
PTE_NX = BIT64(63)                          # execute disable
PTE_PERM_MASK = PTE_P | PTE_W | PTE_U | PTE_PWT | PTE_PCD | PTE_AVL | PTE_NX

DMAR_PTE_R = BIT64(0)     # Read
DMAR_PTE_W = BIT64(1)     # Write
DMAR_PTE_SNP = BIT64(11)  # Snoop Behaviour
DMAR_PTE_TM = BIT64(62)   # Transient Mapping


DMAR_PTE_ADDR_SHIFT = z3.BitVecVal(12, uint64_t)
PTE_PFN_SHIFT = z3.BitVecVal(12, uint64_t)

# defines page type
PGTYPE_PAGE = z3.BitVecVal(0, uint64_t)
PGTYPE_PROC = z3.BitVecVal(1, uint64_t)
PGTYPE_PAGE_DESC = z3.BitVecVal(2, uint64_t)
PGTYPE_FILE_TABLE = z3.BitVecVal(3, uint64_t)
PGTYPE_DEVICES = z3.BitVecVal(4, uint64_t)
PGTYPE_PCIPAGE = z3.BitVecVal(5, uint64_t)
PGTYPE_IOMMU_FRAME = z3.BitVecVal(6, uint64_t)
PGTYPE_NONE = z3.BitVecVal(7, uint64_t)

# defines max page numbers of different type.
NPAGES_PAGES = NPAGE
NPAGES_PROC_TABLE = 6
NPAGES_FILE_TABLE = 2
NPAGES_PAGE_DESC_TABLE = 64
NPAGES_DEVICES = 2


class PCI(Struct):
    owner = Map(devid_t, pid_t)                         # device's process id
    page_table_root = Map(devid_t, pn_t)                # device's page table root


class Vectors(Struct):
    owner = Map(uint8_t, pid_t)                         # interupt vector number corresponding process


class IO(Struct):
    owner = Map(uint16_t, pid_t)                        # IO port to process id.


class Intremap(Struct):                                 # interrupt remmaping
    state = Map(size_t, intremap_state_t)               # 
    devid = Map(size_t, devid_t)
    vector = Map(size_t, uint8_t)                       # address to vector number.


class Page(Struct):
    data = Map(pn_t, uint64_t, uint64_t)                # page num & index --> data; data = page number(52 bit) + permission(12 bit);
    owner = Map(pn_t, pid_t)                            # page --> pid
    type = Map(pn_t, page_type_t)                       # page's type
    pgtable_pn = Map(pn_t, uint64_t, uint64_t)          # (pn, index, pn), i.e.,page number that the page of page table entry i corresponding to .
    pgtable_perm = Map(pn_t, uint64_t, uint64_t)		# (pn, index, perm) page permission that the page of page table entry i corresponding to .
    pgtable_type = Map(pn_t, uint64_t, uint64_t)		# (pn, index, type) page type that the page of page table entry i corresponding to .

    pgtable_reverse_pn = Map(pn_t, pn_t)				# shadow page table
    pgtable_reverse_idx = Map(pn_t, pn_t)				# the front page's page table entry's index.


class DMAPage(Struct):
    owner = Map(pn_t, pid_t)							# the process which owned this page
    type = Map(pn_t, page_type_t)						# the page ty


class PCIPage(Struct):
    owner = Map(pn_t, devid_t)							# the device which owned this page
    valid = Map(pn_t, bool_t)							# is valid or not of this page


class Proc(Struct):
    state = Map(pid_t, proc_state_t)					# the state of process
    ppid = Map(pid_t, pid_t)							# parent process id of process
    killed = Map(pid_t, bool_t)							# killed or not of process

    ipc_from = Map(pid_t, pid_t)						# process --> current process
    ipc_val = Map(pid_t, uint64_t)
    ipc_page = Map(pid_t, pn_t)
    ipc_size = Map(pid_t, size_t)
    ipc_fd = Map(pid_t, fd_t)

    ofile = Map(pid_t, fd_t, fn_t)						# (process, file descriptor, file NO) opened file of process 

    nr_children = Refcnt(pid_t, pid_t, size_t, initial_offset=1) # (process, child prcess, child process' count)
    nr_fds = Refcnt(pid_t, fd_t, size_t)				# opened file descriptor
    nr_pages = Refcnt(pid_t, pn_t, size_t)				# owned page numbers
    nr_dmapages = Refcnt(pid_t, pn_t, size_t)			# owned DMA page numbers
    nr_devs = Refcnt(pid_t, devid_t, size_t)			# owned device numbers
    nr_ports = Refcnt(pid_t, uint16_t, size_t)			# owned IO ports numbers
    nr_vectors = Refcnt(pid_t, uint8_t, size_t)			# owned vector numbers
    nr_intremaps = Refcnt(pid_t, size_t, size_t)		# owned intremap numbers.

    stack = Map(pid_t, pn_t)							# stack coresponding pages
    hvm = Map(pid_t, pn_t)								# hvm page corresponding 
    page_table_root = Map(pid_t, pn_t)					# the page table root 

    use_io_bitmap = Map(pid_t, bool_t)					# use io bitmap or not
    io_bitmap_a = Map(pid_t, pn_t)						# the page which io bitmap a corresponding to 
    io_bitmap_b = Map(pid_t, pn_t)

    intr = Map(pid_t, uint64_t, uint64_t)				# ???????????

    tlbinv = Map(pid_t, bool_t)							# flush tlb or not


class File(Struct):
    type = Map(fn_t, file_type_t)						# the file type which file number corresponding to
    refcnt = Refcnt2(fn_t, (pid_t, fd_t), size_t)		# how to expand use english?
    value = Map(fn_t, uint64_t)
    omode = Map(fn_t, uint64_t)							# opened mode
    offset = Map(fn_t, size_t)							# offset.


"""
Global kernel state for specification
"""
class KernelState(BaseStruct):
    pages_ptr_to_int = Map(uint64_t)					# page start pointer 
    proc_table_ptr_to_int = Map(uint64_t)				# process table pointer 
    page_desc_table_ptr_to_int = Map(uint64_t)			# process descripte table pointer
    file_table_ptr_to_int = Map(uint64_t)				# file table pointer 
    devices_ptr_to_int = Map(uint64_t)					# device pointer
    dmapages_ptr_to_int = Map(uint64_t)					# dma page
	# instance all of kernel object.
    procs = Proc()
    pages = Page()
    dmapages = DMAPage()
    files = File()
    pci = PCI()
    pcipages = PCIPage()
    vectors = Vectors()
    io = IO()
    intremaps = Intremap()
	# current process
    current = Map(pid_t)
    iotlbinv = Map(bool_t)								# flush iotlb or not

    def flush_iotlb(self):
        self.iotlbinv = z3.BoolVal(True)

    def flush_tlb(self, pid):
        self.procs[pid].tlbinv = z3.BoolVal(True)

# useless
def state_to_dict(state, model):
    m = {
        'procs': {},
        'pages': {},
        'current': model.evaluate(state.current).as_long(),
    }
    for p in range(1, NPROC):
        m['procs'][p] = {
            'state': model.evaluate(state.procs[p].state).as_long(),
            # 'ppid': model.evaluate(state.procs[p].ppid).as_long(),
            'page_table_root': model.evaluate(state.procs[p].page_table_root).as_long(),
            # 'nr_pages': model.evaluate(state.procs[p].nr_pages()).as_long(),
        }
    for p in range(0, NPAGE):
        page = {
            'owner': model.evaluate(state.pages[p].owner).as_long(),
            'type': model.evaluate(state.pages[p].type).as_long(),
        }

        if not (0 < page['owner'] < NPAGE):
            continue

        data = {}
        for idx in range(512):
            if model.evaluate(state.pages[p].data(idx) & PTE_P == 0):
                continue
            data[idx] = {}
            data[idx]['val'] = model.evaluate(state.pages[p].data(idx)).as_long()
            data[idx]['resource'] = model.evaluate(state.pages[p].pgtable_pn(idx)).as_long()
            data[idx]['type'] = model.evaluate(state.pages[p].pgtable_type(idx)).as_long()

        page['data'] = data

        m['pages'][p] = page

    return m
