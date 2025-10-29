declare i32 @printf(i8*, ...)

@exit_format = private unnamed_addr constant [29 x i8] c"Program exit with result %d\0A\00", align 1

define void @printResult(i32 %val) {
  %fmt_ptr = getelementptr inbounds [29 x i8], [29 x i8]* @exit_format, i32 0, i32 0
  call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 %val)
  ret void
}


define i32 @main() {
  %a = add i32 0, 100
  %b = add i32 0, 50
  %_temp_0 = sub i32 %a, %b
  %result = add i32 0, %_temp_0
  %_temp_1 = mul i32 %result, 2
  %result.1 = add i32 0, %_temp_1
  call void @printResult(i32 %result.1)
  ret i32 %result.1
}