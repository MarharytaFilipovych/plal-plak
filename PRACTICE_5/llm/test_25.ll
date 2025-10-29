declare i32 @printf(i8*, ...)

@exit_format = private unnamed_addr constant [29 x i8] c"Program exit with result %d\0A\00", align 1

define void @printResult(i32 %val) {
  %fmt_ptr = getelementptr inbounds [29 x i8], [29 x i8]* @exit_format, i32 0, i32 0
  call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 %val)
  ret void
}


define i32 @main() {
  %a = add i1 0, 1
  %_temp_0 = xor i1 %a, 1
  %b = add i1 0, %_temp_0
  br i1 %b, label %then_0, label %end_0
then_0:
  call void @printResult(i32 0)
  ret i32 0
end_0:
  call void @printResult(i32 1)
  ret i32 1
}