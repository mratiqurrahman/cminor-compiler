target triple = "x86_64-pc-linux-gnu"

define i32 @main() {
entry:
  %v_s3 = alloca i32, align 4
  %v_s4 = alloca i32, align 4
  %t0 = add i32 0, 5
  %t1 = call i32 @sum_to(i32 %t0)
  store i32 %t1, ptr %v_s3, align 4
  %t2 = add i32 0, 5
  %t3 = call i32 @factorial(i32 %t2)
  store i32 %t3, ptr %v_s4, align 4
  %t4 = load i32, ptr %v_s3, align 4
  %t5 = add i32 0, 15
  %c0 = icmp ne i32 %t4, %t5
  %t6 = zext i1 %c0 to i32
  %c1 = icmp ne i32 %t6, 0
  br i1 %c1, label %L0, label %L1
L0:
  %t7 = add i32 0, 1
  ret i32 %t7
L1:
  %t8 = load i32, ptr %v_s4, align 4
  %t9 = add i32 0, 120
  %c2 = icmp ne i32 %t8, %t9
  %t10 = zext i1 %c2 to i32
  %c3 = icmp ne i32 %t10, 0
  br i1 %c3, label %L2, label %L3
L2:
  %t11 = add i32 0, 2
  ret i32 %t11
L3:
  %t12 = add i32 0, 0
  ret i32 %t12
}

define i32 @factorial(i32 %arg0) {
entry:
  %v_s5 = alloca i32, align 4
  store i32 %arg0, ptr %v_s5, align 4
  %t0 = load i32, ptr %v_s5, align 4
  %t1 = add i32 0, 1
  %c0 = icmp sle i32 %t0, %t1
  %t2 = zext i1 %c0 to i32
  %c1 = icmp ne i32 %t2, 0
  br i1 %c1, label %L0, label %L1
L0:
  %t3 = add i32 0, 1
  ret i32 %t3
L1:
  %t4 = load i32, ptr %v_s5, align 4
  %t5 = load i32, ptr %v_s5, align 4
  %t6 = add i32 0, 1
  %t7 = sub i32 %t5, %t6
  %t8 = call i32 @factorial(i32 %t7)
  %t9 = mul i32 %t4, %t8
  ret i32 %t9
}

define i32 @sum_to(i32 %arg0) {
entry:
  %v_s6 = alloca i32, align 4
  %v_s7 = alloca i32, align 4
  %v_s8 = alloca i32, align 4
  store i32 %arg0, ptr %v_s6, align 4
  %t0 = add i32 0, 0
  store i32 %t0, ptr %v_s7, align 4
  %t1 = add i32 0, 1
  store i32 %t1, ptr %v_s8, align 4
  br label %L0
L0:
  %t2 = load i32, ptr %v_s8, align 4
  %t3 = load i32, ptr %v_s6, align 4
  %c0 = icmp sle i32 %t2, %t3
  %t4 = zext i1 %c0 to i32
  %c1 = icmp ne i32 %t4, 0
  br i1 %c1, label %L1, label %L3
L1:
  %t5 = load i32, ptr %v_s7, align 4
  %t6 = load i32, ptr %v_s8, align 4
  %t7 = add i32 %t5, %t6
  store i32 %t7, ptr %v_s7, align 4
  br label %L2
L2:
  %t8 = load i32, ptr %v_s8, align 4
  %t9 = add i32 0, 1
  %t10 = add i32 %t8, %t9
  store i32 %t10, ptr %v_s8, align 4
  br label %L0
L3:
  %t11 = load i32, ptr %v_s7, align 4
  ret i32 %t11
}
