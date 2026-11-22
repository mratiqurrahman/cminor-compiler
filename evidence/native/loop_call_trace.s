	.att_syntax
	.file	"module.ll"
	.text
	.globl	main                            # -- Begin function main
	.p2align	4
	.type	main,@function
main:                                   # @main
	.cfi_startproc
# %bb.0:                                # %entry
	pushq	%rax
	.cfi_def_cfa_offset 16
	movl	$5, %edi
	addl	$0, %edi
	callq	sum_to@PLT
	movl	%eax, 4(%rsp)
	movl	$5, %edi
	addl	$0, %edi
	callq	factorial@PLT
	movl	%eax, (%rsp)
	movl	4(%rsp), %eax
	movl	$15, %ecx
	addl	$0, %ecx
	cmpl	%ecx, %eax
	setne	%al
	andb	$1, %al
	movzbl	%al, %eax
	cmpl	$0, %eax
	je	.LBB0_2
# %bb.1:                                # %L0
	movl	$1, %eax
	addl	$0, %eax
	popq	%rcx
	.cfi_def_cfa_offset 8
	retq
.LBB0_2:                                # %L1
	.cfi_def_cfa_offset 16
	movl	(%rsp), %eax
	movl	$120, %ecx
	addl	$0, %ecx
	cmpl	%ecx, %eax
	setne	%al
	andb	$1, %al
	movzbl	%al, %eax
	cmpl	$0, %eax
	je	.LBB0_4
# %bb.3:                                # %L2
	movl	$2, %eax
	addl	$0, %eax
	popq	%rcx
	.cfi_def_cfa_offset 8
	retq
.LBB0_4:                                # %L3
	.cfi_def_cfa_offset 16
	xorl	%eax, %eax
	addl	$0, %eax
	popq	%rcx
	.cfi_def_cfa_offset 8
	retq
.Lfunc_end0:
	.size	main, .Lfunc_end0-main
	.cfi_endproc
                                        # -- End function
	.globl	factorial                       # -- Begin function factorial
	.p2align	4
	.type	factorial,@function
factorial:                              # @factorial
	.cfi_startproc
# %bb.0:                                # %entry
	pushq	%rax
	.cfi_def_cfa_offset 16
	movl	%edi, 4(%rsp)
	movl	4(%rsp), %eax
	movl	$1, %ecx
	addl	$0, %ecx
	cmpl	%ecx, %eax
	setle	%al
	andb	$1, %al
	movzbl	%al, %eax
	cmpl	$0, %eax
	je	.LBB1_2
# %bb.1:                                # %L0
	movl	$1, %eax
	addl	$0, %eax
	popq	%rcx
	.cfi_def_cfa_offset 8
	retq
.LBB1_2:                                # %L1
	.cfi_def_cfa_offset 16
	movl	4(%rsp), %eax
	movl	%eax, (%rsp)                    # 4-byte Spill
	movl	4(%rsp), %edi
	movl	$1, %eax
	addl	$0, %eax
	subl	%eax, %edi
	callq	factorial@PLT
	movl	%eax, %ecx
	movl	(%rsp), %eax                    # 4-byte Reload
	imull	%ecx, %eax
	popq	%rcx
	.cfi_def_cfa_offset 8
	retq
.Lfunc_end1:
	.size	factorial, .Lfunc_end1-factorial
	.cfi_endproc
                                        # -- End function
	.globl	sum_to                          # -- Begin function sum_to
	.p2align	4
	.type	sum_to,@function
sum_to:                                 # @sum_to
	.cfi_startproc
# %bb.0:                                # %entry
	movl	%edi, -4(%rsp)
	xorl	%eax, %eax
	addl	$0, %eax
	movl	%eax, -8(%rsp)
	movl	$1, %eax
	addl	$0, %eax
	movl	%eax, -12(%rsp)
.LBB2_1:                                # %L0
                                        # =>This Inner Loop Header: Depth=1
	movl	-12(%rsp), %eax
	cmpl	-4(%rsp), %eax
	setle	%al
	andb	$1, %al
	movzbl	%al, %eax
	cmpl	$0, %eax
	je	.LBB2_4
# %bb.2:                                # %L1
                                        #   in Loop: Header=BB2_1 Depth=1
	movl	-8(%rsp), %eax
	addl	-12(%rsp), %eax
	movl	%eax, -8(%rsp)
# %bb.3:                                # %L2
                                        #   in Loop: Header=BB2_1 Depth=1
	movl	-12(%rsp), %eax
	movl	$1, %ecx
	addl	$0, %ecx
	addl	%ecx, %eax
	movl	%eax, -12(%rsp)
	jmp	.LBB2_1
.LBB2_4:                                # %L3
	movl	-8(%rsp), %eax
	retq
.Lfunc_end2:
	.size	sum_to, .Lfunc_end2-sum_to
	.cfi_endproc
                                        # -- End function
	.section	".note.GNU-stack","",@progbits
