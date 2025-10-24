declare i32 @printf(i8*, ...)

@exit_format = private unnamed_addr constant [29 x i8] c"Program exit with result %d\0A\00", align 1

define void @printResult(i32 %val) {
  %fmt_ptr = getelementptr inbounds [29 x i8], [29 x i8]* @exit_format, i32 0, i32 0
  call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 %val)
  ret void
}


define i32 @main() {
  %x = add i32 0, 10
  br i1 1, label %then_0, label %end_0
then_0:
  %x.1 = add i1 0, 1
  br i1 %x.1, label %then_1, label %end_1
then_1:
  call void @printResult(i32 5)
  ret i32 5
end_1:
  br label %end_0
end_0:
  call void @printResult(i32 %x)
  ret i32 %x
}