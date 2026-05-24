	.file	"template.2186c4bed7964fa3-cgu.0"
	.section	.text.add_floats,"ax",@progbits
	.globl	add_floats
	.p2align	4
	.type	add_floats,@function
add_floats:
	.cfi_startproc
	addsd	%xmm1, %xmm0
	retq
.Lfunc_end0:
	.size	add_floats, .Lfunc_end0-add_floats
	.cfi_endproc

	.section	.text.add_ints,"ax",@progbits
	.globl	add_ints
	.p2align	4
	.type	add_ints,@function
add_ints:
	.cfi_startproc
	leaq	(%rdi,%rsi), %rax
	addq	$123, %rax
	retq
.Lfunc_end1:
	.size	add_ints, .Lfunc_end1-add_ints
	.cfi_endproc

	.section	.text.call_area,"ax",@progbits
	.globl	call_area
	.p2align	4
	.type	call_area,@function
call_area:
	.cfi_startproc
	jmpq	*24(%rsi)
.Lfunc_end2:
	.size	call_area, .Lfunc_end2-call_area
	.cfi_endproc

	.section	.rodata.cst8,"aM",@progbits,8
	.p2align	3, 0x0
.LCPI3_0:
	.quad	0x3ff0000000000000
	.section	.text.call_tanh,"ax",@progbits
	.globl	call_tanh
	.p2align	4
	.type	call_tanh,@function
call_tanh:
	.cfi_startproc
	pushq	%rax
	.cfi_def_cfa_offset 16
	movapd	%xmm0, %xmm1
	movsd	%xmm0, (%rsp)
	movsd	.LCPI3_0(%rip), %xmm0
	addsd	%xmm1, %xmm0
	callq	*tanh@GOTPCREL(%rip)
	addsd	(%rsp), %xmm0
	popq	%rax
	.cfi_def_cfa_offset 8
	retq
.Lfunc_end3:
	.size	call_tanh, .Lfunc_end3-call_tanh
	.cfi_endproc

	.section	.text.collatz,"ax",@progbits
	.globl	collatz
	.p2align	4
	.type	collatz,@function
collatz:
	.cfi_startproc
	leaq	(%rdi,%rdi,2), %rax
	incq	%rax
	movq	%rdi, %rcx
	sarq	%rcx
	testb	$1, %dil
	cmoveq	%rcx, %rax
	retq
.Lfunc_end4:
	.size	collatz, .Lfunc_end4-collatz
	.cfi_endproc

	.section	.text.gcd1,"ax",@progbits
	.globl	gcd1
	.p2align	4
	.type	gcd1,@function
gcd1:
	.cfi_startproc
	movq	%rdi, %rax
	testq	%rsi, %rsi
	je	.LBB5_6
	movq	%rsi, %rcx
	notq	%rcx
	movabsq	$-9223372036854775808, %rdx
	xorq	%rax, %rdx
	orq	%rcx, %rdx
	je	.LBB5_4
	movq	%rax, %rcx
	orq	%rsi, %rcx
	shrq	$32, %rcx
	je	.LBB5_3
	cqto
	idivq	%rsi
	movq	%rdx, %rax
.LBB5_6:
	retq
.LBB5_3:
	xorl	%edx, %edx
	divl	%esi
	movl	%edx, %eax
	retq
.LBB5_4:
	pushq	%rax
	.cfi_def_cfa_offset 16
	leaq	.Lanon.e495569d849372e26bf80ec87543d5aa.1(%rip), %rdi
	callq	*_ZN4core9panicking11panic_const24panic_const_rem_overflow17h06bd4d0d47e316feE@GOTPCREL(%rip)
.Lfunc_end5:
	.size	gcd1, .Lfunc_end5-gcd1
	.cfi_endproc

	.section	.text.get_float_array3_elem_const,"ax",@progbits
	.globl	get_float_array3_elem_const
	.p2align	4
	.type	get_float_array3_elem_const,@function
get_float_array3_elem_const:
	.cfi_startproc
	movsd	16(%rdi), %xmm0
	retq
.Lfunc_end6:
	.size	get_float_array3_elem_const, .Lfunc_end6-get_float_array3_elem_const
	.cfi_endproc

	.section	.text.get_float_array3_elem_var,"ax",@progbits
	.globl	get_float_array3_elem_var
	.p2align	4
	.type	get_float_array3_elem_var,@function
get_float_array3_elem_var:
	.cfi_startproc
	cmpq	$2, %rsi
	ja	.LBB7_2
	movsd	(%rdi,%rsi,8), %xmm0
	retq
.LBB7_2:
	pushq	%rax
	.cfi_def_cfa_offset 16
	leaq	.Lanon.e495569d849372e26bf80ec87543d5aa.2(%rip), %rdx
	movq	%rsi, %rdi
	movl	$3, %esi
	callq	*_ZN4core9panicking18panic_bounds_check17h58fb035a90e7d970E@GOTPCREL(%rip)
.Lfunc_end7:
	.size	get_float_array3_elem_var, .Lfunc_end7-get_float_array3_elem_var
	.cfi_endproc

	.section	.text.get_float_slice_elem_const,"ax",@progbits
	.globl	get_float_slice_elem_const
	.p2align	4
	.type	get_float_slice_elem_const,@function
get_float_slice_elem_const:
	.cfi_startproc
	cmpq	$3, %rsi
	jb	.LBB8_2
	movsd	16(%rdi), %xmm0
	retq
.LBB8_2:
	pushq	%rax
	.cfi_def_cfa_offset 16
	leaq	.Lanon.e495569d849372e26bf80ec87543d5aa.3(%rip), %rdx
	movl	$2, %edi
	callq	*_ZN4core9panicking18panic_bounds_check17h58fb035a90e7d970E@GOTPCREL(%rip)
.Lfunc_end8:
	.size	get_float_slice_elem_const, .Lfunc_end8-get_float_slice_elem_const
	.cfi_endproc

	.section	.text.get_float_slice_elem_var,"ax",@progbits
	.globl	get_float_slice_elem_var
	.p2align	4
	.type	get_float_slice_elem_var,@function
get_float_slice_elem_var:
	.cfi_startproc
	cmpq	%rsi, %rdx
	jae	.LBB9_2
	movsd	(%rdi,%rdx,8), %xmm0
	retq
.LBB9_2:
	pushq	%rax
	.cfi_def_cfa_offset 16
	leaq	.Lanon.e495569d849372e26bf80ec87543d5aa.4(%rip), %rax
	movq	%rdx, %rdi
	movq	%rax, %rdx
	callq	*_ZN4core9panicking18panic_bounds_check17h58fb035a90e7d970E@GOTPCREL(%rip)
.Lfunc_end9:
	.size	get_float_slice_elem_var, .Lfunc_end9-get_float_slice_elem_var
	.cfi_endproc

	.section	.text.get_point_y,"ax",@progbits
	.globl	get_point_y
	.p2align	4
	.type	get_point_y,@function
get_point_y:
	.cfi_startproc
	movaps	%xmm1, %xmm0
	retq
.Lfunc_end10:
	.size	get_point_y, .Lfunc_end10-get_point_y
	.cfi_endproc

	.section	.text.get_point_y_box,"ax",@progbits
	.globl	get_point_y_box
	.p2align	4
	.type	get_point_y_box,@function
get_point_y_box:
	.cfi_startproc
	pushq	%rax
	.cfi_def_cfa_offset 16
	movsd	8(%rdi), %xmm0
	movsd	%xmm0, (%rsp)
	movl	$16, %esi
	movl	$8, %edx
	callq	*_RNvCs5QKde7ScR4H_7___rustc14___rust_dealloc@GOTPCREL(%rip)
	movsd	(%rsp), %xmm0
	popq	%rax
	.cfi_def_cfa_offset 8
	retq
.Lfunc_end11:
	.size	get_point_y_box, .Lfunc_end11-get_point_y_box
	.cfi_endproc

	.section	.text.get_point_y_ref,"ax",@progbits
	.globl	get_point_y_ref
	.p2align	4
	.type	get_point_y_ref,@function
get_point_y_ref:
	.cfi_startproc
	movsd	8(%rdi), %xmm0
	retq
.Lfunc_end12:
	.size	get_point_y_ref, .Lfunc_end12-get_point_y_ref
	.cfi_endproc

	.section	.text.mk_array_10,"ax",@progbits
	.globl	mk_array_10
	.p2align	4
	.type	mk_array_10,@function
mk_array_10:
	.cfi_startproc
	movq	%rdi, %rax
	movaps	%xmm0, %xmm1
	movlhps	%xmm0, %xmm1
	movups	%xmm1, 16(%rdi)
	movups	%xmm1, (%rdi)
	movups	%xmm1, 48(%rdi)
	movups	%xmm1, 32(%rdi)
	movsd	%xmm0, 64(%rdi)
	movsd	%xmm0, 72(%rdi)
	retq
.Lfunc_end13:
	.size	mk_array_10, .Lfunc_end13-mk_array_10
	.cfi_endproc

	.section	.rodata.cst8,"aM",@progbits,8
	.p2align	3, 0x0
.LCPI14_0:
	.quad	0x3ff0000000000000
.LCPI14_1:
	.quad	0x4000000000000000
	.section	.text.mk_point,"ax",@progbits
	.globl	mk_point
	.p2align	4
	.type	mk_point,@function
mk_point:
	.cfi_startproc
	addsd	.LCPI14_0(%rip), %xmm0
	addsd	.LCPI14_1(%rip), %xmm1
	retq
.Lfunc_end14:
	.size	mk_point, .Lfunc_end14-mk_point
	.cfi_endproc

	.section	.rodata.cst16,"aM",@progbits,16
	.p2align	4, 0x0
.LCPI15_0:
	.quad	0x3ff0000000000000
	.quad	0x4000000000000000
	.section	.text.mk_point_box,"ax",@progbits
	.globl	mk_point_box
	.p2align	4
	.type	mk_point_box,@function
mk_point_box:
	.cfi_startproc
	subq	$40, %rsp
	.cfi_def_cfa_offset 48
	movaps	%xmm1, (%rsp)
	movaps	%xmm0, 16(%rsp)
	callq	*_RNvCs5QKde7ScR4H_7___rustc35___rust_no_alloc_shim_is_unstable_v2@GOTPCREL(%rip)
	movl	$16, %edi
	movl	$8, %esi
	callq	*_RNvCs5QKde7ScR4H_7___rustc12___rust_alloc@GOTPCREL(%rip)
	testq	%rax, %rax
	je	.LBB15_2
	movapd	16(%rsp), %xmm0
	unpcklpd	(%rsp), %xmm0
	addpd	.LCPI15_0(%rip), %xmm0
	movupd	%xmm0, (%rax)
	addq	$40, %rsp
	.cfi_def_cfa_offset 8
	retq
.LBB15_2:
	.cfi_def_cfa_offset 48
	movl	$8, %edi
	movl	$16, %esi
	callq	*_ZN5alloc5alloc18handle_alloc_error17h5e5a04c38c89a5bbE@GOTPCREL(%rip)
.Lfunc_end15:
	.size	mk_point_box, .Lfunc_end15-mk_point_box
	.cfi_endproc

	.section	.text.mk_vec_10,"ax",@progbits
	.globl	mk_vec_10
	.p2align	4
	.type	mk_vec_10,@function
mk_vec_10:
	.cfi_startproc
	pushq	%rbx
	.cfi_def_cfa_offset 16
	subq	$16, %rsp
	.cfi_def_cfa_offset 32
	.cfi_offset %rbx, -16
	movaps	%xmm0, (%rsp)
	movq	%rdi, %rbx
	callq	*_RNvCs5QKde7ScR4H_7___rustc35___rust_no_alloc_shim_is_unstable_v2@GOTPCREL(%rip)
	movl	$80, %edi
	movl	$8, %esi
	callq	*_RNvCs5QKde7ScR4H_7___rustc12___rust_alloc@GOTPCREL(%rip)
	testq	%rax, %rax
	je	.LBB16_2
	movaps	(%rsp), %xmm1
	movaps	%xmm1, %xmm0
	movlhps	%xmm1, %xmm0
	movups	%xmm0, 16(%rax)
	movups	%xmm0, (%rax)
	movups	%xmm0, 48(%rax)
	movups	%xmm0, 32(%rax)
	movsd	%xmm1, 64(%rax)
	movsd	%xmm1, 72(%rax)
	movq	$10, (%rbx)
	movq	%rax, 8(%rbx)
	movq	$10, 16(%rbx)
	movq	%rbx, %rax
	addq	$16, %rsp
	.cfi_def_cfa_offset 16
	popq	%rbx
	.cfi_def_cfa_offset 8
	retq
.LBB16_2:
	.cfi_def_cfa_offset 32
	movl	$8, %edi
	movl	$80, %esi
	callq	*_ZN5alloc5alloc18handle_alloc_error17h5e5a04c38c89a5bbE@GOTPCREL(%rip)
.Lfunc_end16:
	.size	mk_vec_10, .Lfunc_end16-mk_vec_10
	.cfi_endproc

	.section	.text.sum_array_loop,"ax",@progbits
	.globl	sum_array_loop
	.p2align	4
	.type	sum_array_loop,@function
sum_array_loop:
	.cfi_startproc
	testq	%rdx, %rdx
	je	.LBB17_1
	leaq	-1(%rdx), %rax
	cmpq	%rax, %rsi
	jbe	.LBB17_11
	movl	%edx, %eax
	andl	$7, %eax
	cmpq	$8, %rdx
	jae	.LBB17_9
	xorpd	%xmm0, %xmm0
	xorl	%ecx, %ecx
	jmp	.LBB17_5
.LBB17_1:
	xorps	%xmm0, %xmm0
	retq
.LBB17_9:
	andq	$-8, %rdx
	xorpd	%xmm0, %xmm0
	xorl	%ecx, %ecx
	.p2align	4
.LBB17_10:
	addsd	(%rdi,%rcx,8), %xmm0
	addsd	8(%rdi,%rcx,8), %xmm0
	addsd	16(%rdi,%rcx,8), %xmm0
	addsd	24(%rdi,%rcx,8), %xmm0
	addsd	32(%rdi,%rcx,8), %xmm0
	addsd	40(%rdi,%rcx,8), %xmm0
	addsd	48(%rdi,%rcx,8), %xmm0
	addsd	56(%rdi,%rcx,8), %xmm0
	addq	$8, %rcx
	cmpq	%rcx, %rdx
	jne	.LBB17_10
.LBB17_5:
	testq	%rax, %rax
	je	.LBB17_8
	leaq	(%rdi,%rcx,8), %rcx
	xorl	%edx, %edx
	.p2align	4
.LBB17_7:
	addsd	(%rcx,%rdx,8), %xmm0
	incq	%rdx
	cmpq	%rdx, %rax
	jne	.LBB17_7
.LBB17_8:
	retq
.LBB17_11:
	pushq	%rax
	.cfi_def_cfa_offset 16
	leaq	.Lanon.e495569d849372e26bf80ec87543d5aa.5(%rip), %rdx
	movq	%rsi, %rdi
	callq	*_ZN4core9panicking18panic_bounds_check17h58fb035a90e7d970E@GOTPCREL(%rip)
.Lfunc_end17:
	.size	sum_array_loop, .Lfunc_end17-sum_array_loop
	.cfi_endproc

	.section	.text.sum_array_rec,"ax",@progbits
	.globl	sum_array_rec
	.p2align	4
	.type	sum_array_rec,@function
sum_array_rec:
	.cfi_startproc
	pushq	%r15
	.cfi_def_cfa_offset 16
	pushq	%r14
	.cfi_def_cfa_offset 24
	pushq	%rbx
	.cfi_def_cfa_offset 32
	.cfi_offset %rbx, -32
	.cfi_offset %r14, -24
	.cfi_offset %r15, -16
	testq	%rdx, %rdx
	je	.LBB18_1
	movq	%rdx, %rbx
	movq	%rsi, %r14
	movq	%rdi, %r15
	decq	%rdx
	callq	*sum_array_rec@GOTPCREL(%rip)
	cmpq	%r14, %rbx
	jae	.LBB18_5
	addsd	(%r15,%rbx,8), %xmm0
	popq	%rbx
	.cfi_def_cfa_offset 24
	popq	%r14
	.cfi_def_cfa_offset 16
	popq	%r15
	.cfi_def_cfa_offset 8
	retq
.LBB18_1:
	.cfi_def_cfa_offset 32
	xorps	%xmm0, %xmm0
	popq	%rbx
	.cfi_def_cfa_offset 24
	popq	%r14
	.cfi_def_cfa_offset 16
	popq	%r15
	.cfi_def_cfa_offset 8
	retq
.LBB18_5:
	.cfi_def_cfa_offset 32
	leaq	.Lanon.e495569d849372e26bf80ec87543d5aa.6(%rip), %rdx
	movq	%rbx, %rdi
	movq	%r14, %rsi
	callq	*_ZN4core9panicking18panic_bounds_check17h58fb035a90e7d970E@GOTPCREL(%rip)
.Lfunc_end18:
	.size	sum_array_rec, .Lfunc_end18-sum_array_rec
	.cfi_endproc

	.section	.text.sum_array_tail,"ax",@progbits
	.globl	sum_array_tail
	.p2align	4
	.type	sum_array_tail,@function
sum_array_tail:
	.cfi_startproc
	cmpq	%rcx, %rdx
	je	.LBB19_3
	.p2align	4
.LBB19_1:
	cmpq	%rsi, %rdx
	jae	.LBB19_4
	addsd	(%rdi,%rdx,8), %xmm0
	incq	%rdx
	cmpq	%rdx, %rcx
	jne	.LBB19_1
.LBB19_3:
	retq
.LBB19_4:
	pushq	%rax
	.cfi_def_cfa_offset 16
	leaq	.Lanon.e495569d849372e26bf80ec87543d5aa.7(%rip), %rax
	movq	%rdx, %rdi
	movq	%rax, %rdx
	callq	*_ZN4core9panicking18panic_bounds_check17h58fb035a90e7d970E@GOTPCREL(%rip)
.Lfunc_end19:
	.size	sum_array_tail, .Lfunc_end19-sum_array_tail
	.cfi_endproc

	.type	.Lanon.e495569d849372e26bf80ec87543d5aa.0,@object
	.section	.rodata.str1.1,"aMS",@progbits,1
.Lanon.e495569d849372e26bf80ec87543d5aa.0:
	.asciz	"rs/template.rs"
	.size	.Lanon.e495569d849372e26bf80ec87543d5aa.0, 15

	.type	.Lanon.e495569d849372e26bf80ec87543d5aa.1,@object
	.section	.data.rel.ro..Lanon.e495569d849372e26bf80ec87543d5aa.1,"aw",@progbits
	.p2align	3, 0x0
.Lanon.e495569d849372e26bf80ec87543d5aa.1:
	.quad	.Lanon.e495569d849372e26bf80ec87543d5aa.0
	.asciz	"\016\000\000\000\000\000\000\000J\000\000\000\005\000\000"
	.size	.Lanon.e495569d849372e26bf80ec87543d5aa.1, 24

	.type	.Lanon.e495569d849372e26bf80ec87543d5aa.2,@object
	.section	.data.rel.ro..Lanon.e495569d849372e26bf80ec87543d5aa.2,"aw",@progbits
	.p2align	3, 0x0
.Lanon.e495569d849372e26bf80ec87543d5aa.2:
	.quad	.Lanon.e495569d849372e26bf80ec87543d5aa.0
	.asciz	"\016\000\000\000\000\000\000\000-\000\000\000\005\000\000"
	.size	.Lanon.e495569d849372e26bf80ec87543d5aa.2, 24

	.type	.Lanon.e495569d849372e26bf80ec87543d5aa.3,@object
	.section	.data.rel.ro..Lanon.e495569d849372e26bf80ec87543d5aa.3,"aw",@progbits
	.p2align	3, 0x0
.Lanon.e495569d849372e26bf80ec87543d5aa.3:
	.quad	.Lanon.e495569d849372e26bf80ec87543d5aa.0
	.asciz	"\016\000\000\000\000\000\000\0002\000\000\000\005\000\000"
	.size	.Lanon.e495569d849372e26bf80ec87543d5aa.3, 24

	.type	.Lanon.e495569d849372e26bf80ec87543d5aa.4,@object
	.section	.data.rel.ro..Lanon.e495569d849372e26bf80ec87543d5aa.4,"aw",@progbits
	.p2align	3, 0x0
.Lanon.e495569d849372e26bf80ec87543d5aa.4:
	.quad	.Lanon.e495569d849372e26bf80ec87543d5aa.0
	.asciz	"\016\000\000\000\000\000\000\0007\000\000\000\005\000\000"
	.size	.Lanon.e495569d849372e26bf80ec87543d5aa.4, 24

	.type	.Lanon.e495569d849372e26bf80ec87543d5aa.5,@object
	.section	.data.rel.ro..Lanon.e495569d849372e26bf80ec87543d5aa.5,"aw",@progbits
	.p2align	3, 0x0
.Lanon.e495569d849372e26bf80ec87543d5aa.5:
	.quad	.Lanon.e495569d849372e26bf80ec87543d5aa.0
	.asciz	"\016\000\000\000\000\000\000\000T\000\000\000\n\000\000"
	.size	.Lanon.e495569d849372e26bf80ec87543d5aa.5, 24

	.type	.Lanon.e495569d849372e26bf80ec87543d5aa.6,@object
	.section	.data.rel.ro..Lanon.e495569d849372e26bf80ec87543d5aa.6,"aw",@progbits
	.p2align	3, 0x0
.Lanon.e495569d849372e26bf80ec87543d5aa.6:
	.quad	.Lanon.e495569d849372e26bf80ec87543d5aa.0
	.asciz	"\016\000\000\000\000\000\000\000g\000\000\000\037\000\000"
	.size	.Lanon.e495569d849372e26bf80ec87543d5aa.6, 24

	.type	.Lanon.e495569d849372e26bf80ec87543d5aa.7,@object
	.section	.data.rel.ro..Lanon.e495569d849372e26bf80ec87543d5aa.7,"aw",@progbits
	.p2align	3, 0x0
.Lanon.e495569d849372e26bf80ec87543d5aa.7:
	.quad	.Lanon.e495569d849372e26bf80ec87543d5aa.0
	.asciz	"\016\000\000\000\000\000\000\000r\000\000\000%\000\000"
	.size	.Lanon.e495569d849372e26bf80ec87543d5aa.7, 24

	.ident	"rustc version 1.94.0 (4a4ef493e 2026-03-02)"
	.section	".note.GNU-stack","",@progbits
