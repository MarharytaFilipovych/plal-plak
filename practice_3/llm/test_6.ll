declare i32 @printf(i8*, ...)

@exit_format = private unnamed_addr constant [29 x i8] c"Program exit with result %d\0A\00", align 1

define void @printResult(i32 %val) {
  %fmt_ptr = getelementptr inbounds [29 x i8], [29 x i8]* @exit_format, i32 0, i32 0
  call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 %val)
  ret void
}


define i32 @main() {
  %value = add i32 0, 42
  %_temp_129753032670032 = mul i32 %value, 2
  %result = add i32 0, %_temp_129753032670032
  call void @printResult(i32 %result)
  ret i32 %result
}