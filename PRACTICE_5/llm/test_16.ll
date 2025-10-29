declare i32 @printf(i8*, ...)

@exit_format = private unnamed_addr constant [29 x i8] c"Program exit with result %d\0A\00", align 1

define void @printResult(i32 %val) {
  %fmt_ptr = getelementptr inbounds [29 x i8], [29 x i8]* @exit_format, i32 0, i32 0
  call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 %val)
  ret void
}


define i32 @main() {
  %small = add i32 0, 100
  %_temp_0 = sext i32 100 to i64
  %large = add i64 0, %_temp_0
  %_temp_2 = sext i32 %small to i64
  %_temp_1 = icmp eq i64 %_temp_2, %large
  %areEqual = add i1 0, %_temp_1
  %_temp_3 = zext i1 %areEqual to i32
  call void @printResult(i32 %_temp_3)
  ret i32 %_temp_3
}