declare i32 @printf(i8*, ...)

@exit_format = private unnamed_addr constant [29 x i8] c"Program exit with result %d\0A\00", align 1

define void @printResult(i32 %val) {
  %fmt_ptr = getelementptr inbounds [29 x i8], [29 x i8]* @exit_format, i32 0, i32 0
  call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 %val)
  ret void
}


define i32 @main() {
  %a = add i32 0, 5
  %b = add i32 0, 3
  %_temp_0 = add i32 %a, %b
  %c = add i32 0, %_temp_0
  call void @printResult(i32 %c)
  ret i32 %c
}