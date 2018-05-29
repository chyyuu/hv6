# analysis
本文主要针对规约中包含的相应文件进行分析，主要关注内核的相关规约
## specification 结构
Hv6/hv6/spec/
	base.py				// 基础数据结构(struct, Map, Refcnt等等)
Hv6/hv6/spec/kernel
	datatypes.py			// os内核数据对象以及状态机(process, pages, IO ports等等)
	main.py				// 系统验证过程的入口，所有的测试用例都在该文件中。
	syscall_spec.py			// 通过调用该文件中的各个系统调用接口，获取syscall相应的参数。用于符号执行。
Hv6/hv6/spec/kernel/spec
	equiv.py			// hv6.py与specification之间的等价函数
	helpers.py			// 提供了一些共同方法，如：进程编号是否合法等
	__init__.py
	invariants.py			// 规约以及程序的不变量，如：从始至终，进程的页表，hvm以及stack都必须是合法的等等。
	specs.py			// syscall对应的所有规约信息,
	top.py				// 上层的cross-cutting属性。如：进程pid拥有的子进程个数一定等于将pid作为父进程的子进程的和。

## base.py

base.py 中包含了八个Class，对关键的几个加以说明：

### Struct
该类中包含了一个__metaclass__成员，并通过StructMeta进行赋值，即StructMeta是Struct类的元类。这就意味着，在包含base.py模块的时候，尽管不进行任何代码的编写，也会执行StructMeta类中的__new__方法。StructMeta类中基本思想是获得Struct类中所有函数和属性，并根据这些函数或者属性中是否包含‘_init’，并将包含'_init'的属性和函数（这里就是Map、refcnt等数据结构）组织成一个字典dct['_meta']，返回给Struct；在Struct中就可以针对这个字典(就是_meta属性)进行操作了。
所有继承Struct类的子类，都会在定义的时候，就执行__metaclass__中的init函数，来初始化子类。
Struct类中包含了一个很重要的_init(sefl, parent, name)方法，该方法主要负责初始化Struct类中的所有对象（stack、proc、pages 之类的）。

### BaseStruct
由于baseStruct继承了Struct，并且在__init__方法中调用了_init方法，所以间接的初始化kernelState的所有Map和refcnt对象。

### Map
一般的map对象都是类似map(A,B)，其中A代表Key，B代表Value。而在hv6中对map多了一层定义，即map可以映射多个数据类型，如：map(A, B, C)，也可以只有一个变量，即map(A)。其中，map(A, B, C)代表由Key A, B -->C；map(A): A类型的变量。Map继承了AbstractMap，同时AbstractMap继承了Accessor，在子类中包含了__get__、__set__ __iadd__ __isub__、__getitem__ __setitem__等方法，所以，Map支持+、-操作以及通过instance.[key]方式获得相关value。

### Refcnt
Refcnt类型的格式为Refcnt(A, B, C)，由于Refcnt继承Map，所以，A，B代表Key，C代表val。这里的Val是数字类型，代表个数。Refcnt的参数个数必须为3，A:owner; B:owned; C:size.
Refcnt类型提供了check函数返回一个conj，这个conj中包含了Refcnt类型应该满足的条件，包含：有效的owner和owned-->(引用个数 < max_refs); 2, 满足双射()；3, 如果A拥有B，f(owned) < ref, 否则 f(owned) >= ref； 4, ref的个数一定是在0~max_refs之间；5，如果refcount == 0， 那么owner不会拥有任何的owned；6， 如果refcount == max_refs，则说明owner拥有所有该资源。即，符合论文提出的资源的排他共享和资源管理等特性。
PS: 需要学习一下Z3.function

## datatype.py

datatype中定义了内核空间的所有对象，如：进程、设备、页、文件等等，同时也定义了所有的数据类型以及全局变量.
Datatype中将这些内核对象集合到一个struct中，构建成os的内核空间状态机KernelState。


### _populate_enums()函数的使用
该函数的目的是通过llvm metadata中数据来初始化相关信息，主要包括page_type_t、file_type_t、proc_state_t和intremap_state_t

### 定义系统常量
包含页大小、页个数、页类型、进程个数、文件个数、PCI设备个数等。进程个数与进程描述表个数一致，都为64.具体信息查看github上对应的注释说明。

### 将C中的常用数据类型用z3py中的数据类型进行转换，同时，这些数据类型都是变量，在符号执行时使用。

page number
pn_t = z3.BitVecSort(64)	//定义了一个64bit长的字节向量变量

### 举例说明

class Page(Struct):
//data: Map(页号, index, data), 指定页号页中第index个entry的值。这个值的格式如下：
// |---------------------|---------|
// |     page number     |   perm  |
// |         52          |   12    |
data = Map(pn_t, uint64_t, uint64_t)

// 该页属于哪个进程
owner = Map(pn_t, pid_t)

// 该页的类型
type = Map(pn_t, page_type_t)

// pgtable_pn: Map(页号, index, 页号)
// 本页中，存储在index中的页号对应的下一级页的页号。这里涉及到两个页号，这个页号存在以下对应关系：
// 页号 =  pages_ptr_to_int / PAGE_SIZE + 页号
pgtable_pn = Map(pn_t, uint64_t, uint64_t)

// 本页中，存储在index中的页号对应的下一级页的permission
// pgtable_perm: Map(页号, index, permission）
pgtable_perm = Map(pn_t, uint64_t, uint64_t)

// 本页中，存储在index中的页号对应的下一级页的页类型，在这里page_type_t与uint64_t是一个数据类型。
// pgtable_type: Map(页号, index, page_type）
pgtable_type = Map(pn_t, uint64_t, uint64_t)

// 本页对应的上一级页表的页号
pgtable_reverse_pn = Map(pn_t, pn_t)

// 本页对应的上一级页表的index
pgtable_reverse_idx = Map(pn_t, pn_t)

## main.py
	main.py是测试用例的入口文件。
该文件中包含了一些实现代码中需要对应的函数，如panic、memcpy、bzero等。这些函数直接作为context中的全局函数来使用。
main.py包含了6个class，针对它们进行分析

### class HV6Meta
该类是HV6Base的__metaclass__类，其作用是通过_syscalls队列生成所有的测试用例。在这些测试用例中，都会调用父类中的_syscal_generic 方法。

### class HV6Base(unittest.TestCase)
该类中是包含了一个函数_prove(cond, pre), 它根据cond和pre调用z3.solver来进行判断，cond为一节逻辑表达式，pre为前置条件。sovler添加z3.Not(cond)后，调用solver.check()方法，如果在验证的结果不等于z3.unsat，则说明验证失败。我们需要通过查找cond中的子集来缩小范围，确定是哪个地方不满足要求。

### class HV6(HV6Base):
该类继承了HV6Base，所以，在该类中也包含了所有的测试用例，同时，也符合单元测试类的要求，在该类中定义了setUp、tearDown，以及一堆的test_syscall方法。在未指定具体的测试项时，系统会直接运行setUp--> test_syscalls-->tearDown方法。所有的test_syscalls中都调用了_syscall_generic方法，在这个方法中，需要获取该syscall的参数，动态执行spcification中对应的syscall，动态执行hv6.py中的syscall，分别得到前置条件以及执行后的新的状态空间，通过equiv.py中定义的state_equiv函数判断执行后的状态空间是等价的，同时判断前置条件也是等价的。
model = self._prove(z3.And(spec.state_equiv(self.ctx, newstate),		//符号执行后状态空间等价
		cond == (res == util.i32(0))),					// 约束条件等价
                            pre=z3.And(self._pre_state, z3.BoolVal(True)),	// 状态机的初始化状态为真
                            return_model=INTERACTIVE)
def setUp(self):
self.ctx = newctx()										// 实例化contex，根据hv6.py对ctx进行赋值，并且设置相关全局函数
self.state = dt.KernelState()									// 状态机
self.solver = Solver()										// 解析器
self.solver.set(AUTO_CONFIG=False)							// 设置解析器相关配置
self._pre_state = spec.state_equiv(self.ctx, self.state)			// 定义spec和hv6.py初始化状态是否等
self.ctx.add_assumption(spec.impl_invariants(self.ctx))			//添加代码的不变量约束条件待hv6.py中
self.solver.add(self._pre_state)								// 确保初始状态 ==  true

### class HV6ImplInvs(HV6Base):
该类测试spec python和C实现的不变量是否一致

### class HV6SpecMeta(HV6Meta):
该类继承HV6Meta，所以它获取所有的syscall信息、lemmas信息、corollaries信息，并通过这些信息来生成测试用例。在这里，测试用例的例子：
lemma：
	def test_'syscall'_'lemma':
		_check_invariant('syscall','lemma')
	def test_'lemma'_initial:
		_check_initial('lemma')
corollaries:
	def test_'pre'_implies_'post':
		_check_corollary('pre','post')

### class HV6TopLemmas(HV6Base):
该类继承了HV6Base，所以，也继承了单元测试类。它定义了setUp、tearDown和很多以test开头的测试用例，测试用例是由上面的meta类来进行初始化的。验证lemmas的主要方法包含个函数：_check_invariant和_check_initial.

// 检查系统调用满足lemma
def _check_invariant(self, syscall, lemma):
        inv = getattr(spec, 'spec_lemma_{}'.format(lemma))					// 从top.py中获取该lemma
        args = syscall_spec.get_syscall_args(syscall)						// 从syscall_spec.py中找到对应syscall的参数

        kwargs = {}
        if 'syscall' in inspect.getargspec(inv)[0]:							// 获取lemma的syscall参数
            kwargs['syscall'] = syscall
        if 'oldstate' in inspect.getargspec(inv)[0]:							// 获取lemma中的oldstate参数
            kwargs['oldstate'] = self.state

        pre = z3.And(spec.spec_invariants(self.state), inv(self.state, **kwargs))// pre-condition,满足spec的不变量，同时满足该引理
        self.solver.add(pre)											// 将pre-condition添加到求解器中
        cond, newstate = getattr(spec, syscall)(self.state, *args)			// 符号执行spec中的syscall
// 验证符号执行后的所有状态空间都满足spec不变量，同时也满足该引理. 这样就需要做交叉组合，可以生成很多测试用例
        model = self._prove(z3.And(spec.spec_invariants(newstate), inv(newstate, **kwargs)),
                            pre=pre, return_model=INTERACTIVE, minimize=MODEL_HI)

// 检查引理的正确性，可以推出推理满足妖气
def _check_corollary(self, pre, post):
        pre = getattr(spec, 'spec_lemma_{}'.format(pre))					// 根据名称获得引理
        post = getattr(spec, 'spec_corollary_{}'.format(post))				// 根据名称获得推理
// 验证：（引理 && spec不变量） ==> 推理
        self._prove(z3.Implies(z3.And(pre(self.state), spec.spec_invariants(self.state)),
                               post(self.state)))

        self.setUp()				// 重新实例化状态机和sovler

        self.state = self.state.initial()									// 初始化当前状态机
        constraints = z3.And(spec.spec_invariants(self.state), post(self.state))// 约束：初始化状态机满足spec的不变量，同时，状态机满足推理约束
        self.solver.add(constraints)
        self.assertEquals(self.solver.check(), z3.sat)						//检查是否能找到相应的满足要求的case

// 初始化状态机是否满足lemma
def _check_initial(self, lemma):
        self.state = self.state.initial()									// 初始化当前状态机，这个函数需要仔细分析一下!!!
        inv = getattr(spec, 'spec_lemma_{}'.format(lemma))					// 根据名称获得对应的引理
        constraints = z3.And(spec.spec_invariants(self.state), inv(self.state))	// 约束：状态机满足spec不变量，同时， 状态机满足引理
        self.solver.add(constraints)										// 添加约束到求解器
        self.assertEquals(self.solver.check(), z3.sat)						// 求解，看是否能找到case

测试用例的执行
单个测试为例：
首先测试的command line为python2 o.x86_64/hv6/hv6py/kernel/spec/main.py -v --failfast HV6.test_sys_set_runnable. 其中 -v：代表verbose，即输出详细信息；--failfast：在出现错误的情况下立刻退出。HV6.test_sys_set_runnable代表执行class HV6这个类下面的test_sys_set_runnable函数。
并行执行测试用例：
python2 scripts/pytest -v --duration=10 --full-trace -r fEsxX --color=auto -n=auto --boxed $(HV6PY)/kernel/spec/main.py::HV6 \
$(HV6PY)/kernel/spec/main.py::HV6TopLemmas \
$(HV6PY)/kernel/spec/main.py::HV6ImplInvs $(ARGS)
--duration: 限制一个测试用例的运行时间？

### 很多基本函数的定义
	

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
