# analysis

## proc related syscalls

### sys_set_runnable

### sys_switch

### sys_kill

### sys_reparent

##  mem related syscalls

### sys_reclaim_page

###  sys_alloc_pdpt

### alloc pate table directory

### sys_alloc_pd 

### alloc page table

### sys_alloc_frame

### sys_copy_frame

### sys_protect_frame

### sys_set_proc_name

### sys_reap

###  sys_map_proc

### sys_map_pml4

### sys_map_page_desc

###  sys_map_dev

###  sys_map_file

### sys_free_pdpt

###  sys_free_pd

###  sys_free_pt

### sys_free_frame

## file related syscalls

### sys_create  //a file

### sys_close

### sys_dup

### sys_dup2

### sys_lseek

## IPC related syscalls

###  sys_send

### sys_recv 

###  sys_reply_wait

###  sys_call

## device related syscalls

### sys_map_pcipage

### sys_alloc_iommu_root 

### sys_alloc_iommu_pdpt

### sys_alloc_iommu_pd

### sys_alloc_iommu_pt

### sys_alloc_iommu_frame

###  sys_map_iommu_frame

###  sys_reclaim_iommu_frame

###  sys_reclaim_iommu_root

### sys_alloc_vector

### sys_reclaim_vector

### sys_alloc_intremap

### sys_reclaim_intremap

### sys_ack_intr

### sys_alloc_io_bitmap

### sys_alloc_port

### sys_reclaim_port
