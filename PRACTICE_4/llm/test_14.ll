declare i32 @printf(i8*, ...)

@exit_format = private unnamed_addr constant [29 x i8] c"Program exit with result %d\0A\00", align 1

define void @printResult(i32 %val) {
  %fmt_ptr = getelementptr inbounds [29 x i8], [29 x i8]* @exit_format, i32 0, i32 0
  call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 %val)
  ret void
}


define i32 @main() {
  %big = add i64 0, 5000000000
  %small = add i32 0, 100
  %_temp_1 = sext i32 %small to i64
  %_temp_0 = add i64 %big, %_temp_1
  %sum = add i64 0, %_temp_0
  %_temp_2 = icmp eq i64 %sum, 5000000100
  %isEqual = add i1 0, %_temp_2
  %counter = add i32 0, 0
  %_temp_3 = add i32 %counter, 1
  %counter.1 = add i32 0, %_temp_3
  call void @printResult(i32 %counter.1)
  ret i32 %counter.1
}