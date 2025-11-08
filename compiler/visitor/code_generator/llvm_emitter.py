#!/usr/bin/env python3


class LLVMEmitter:
    def __init__(self):
        self.translated_lines: list[str] = []
        self.struct_type_lines: list[str] = []
        self.function_definitions: list[str] = []
        self.temp_counter = 0
        self.label_counter = 0

    def emit_line(self, line: str):
        self.translated_lines.append(line)

    def get_temp_register(self) -> str:
        reg = f"%_temp_{self.temp_counter}"
        self.temp_counter += 1
        return reg

    def get_next_label_id(self) -> int:
        label_id = self.label_counter
        self.label_counter += 1
        return label_id

    def emit_label(self, label: str):
        self.translated_lines.append(f"{label}:")

    def add_struct_type_definition(self, struct_def: str):
        self.struct_type_lines.append(struct_def)

    def add_function_definition(self, lines: list[str]):
        self.function_definitions.extend(lines)

    def build_final_output(self) -> str:
        result = [self._get_print_function_llvm()]

        if self.struct_type_lines:
            result.extend(self.struct_type_lines)
            result.append("")

        if self.function_definitions:
            result.extend(self.function_definitions)
            result.append("")

        result.append("define i32 @main() {")
        result.extend(self.translated_lines)
        result.append("}")

        return "\n".join(result)

    @staticmethod
    def _get_print_function_llvm() -> str:
        return """declare i32 @printf(i8*, ...)

@exit_format = private unnamed_addr constant [29 x i8] c"Program exit with result %d\\0A\\00", align 1

define void @printResult(i32 %val) {
  %fmt_ptr = getelementptr inbounds [29 x i8], [29 x i8]* @exit_format, i32 0, i32 0
  call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 %val)
  ret void
}

"""

    def reset_for_function(self):
        self.translated_lines = []
        self.temp_counter = 0
        self.label_counter = 0

    def copy_state(self) -> dict:
        return {
            'translated_lines': self.translated_lines,
            'temp_counter': self.temp_counter,
            'label_counter': self.label_counter
        }

    def restore_state(self, state: dict):
        self.translated_lines = state['translated_lines']
        self.temp_counter = state['temp_counter']
        self.label_counter = state['label_counter']