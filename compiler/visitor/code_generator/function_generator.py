#!/usr/bin/env python3
from typing import Optional
from ...llvm_specifics.data_type import DataType


class FunctionGenerator:
    def __init__(self, emitter, variable_registry, type_converter, struct_ops):
        self.emitter = emitter
        self.variable_registry = variable_registry
        self.type_converter = type_converter
        self.struct_ops = struct_ops
        self.function_return_types = {}
        self.current_struct_context: Optional[str] = None
        self.in_function = False

    def generate_standalone_function(self, node, visitor):
        self.__prepare_function_context(node.variable, node.return_type)
        func_signature = self.__build_function_signature(node)
        self.__initialize_function_body(node, visitor, func_signature)
        self.__finalize_function()

    def __finalize_function(self):
        self.__restore_state(self._saved_state)
        self.in_function = False

    def generate_member_function(self, struct_name: str, node, visitor):
        mangled_name = f"{struct_name}_{node.variable}"
        self.__prepare_function_context(mangled_name, node.return_type)

        func_signature = self.__build_member_function_signature(struct_name, node, mangled_name)
        self.__setup_this_context(struct_name)
        self.__initialize_function_body(node, visitor, func_signature)

        self.current_struct_context = None
        self.__finalize_function()

    def generate_regular_function_call(self, node, visitor) -> str:
        args = [self.__build_call_argument(arg, visitor) for arg in node.arguments]
        result_reg = self.emitter.get_temp_register()
        return_type = self.type_converter.get_node_type(node)

        return_llvm_type = self.__get_function_return_llvm_type(return_type)
        self.emitter.emit_line(f"  {result_reg} = call {return_llvm_type} @{node.value}({', '.join(args)})")
        return result_reg

    def generate_member_function_call(self, node, visitor) -> str:
        object_chain = node.field_chain
        struct_type = self.type_converter.get_object_type_from_chain(object_chain)
        object_ptr = self.struct_ops.get_object_pointer_from_chain(object_chain)
        mangled_name = f"{struct_type}_{node.value}"

        arg_strs = [f"%struct.{struct_type}* {object_ptr}"] + [
            self.__build_call_argument(arg, visitor) for arg in node.arguments]

        result_reg = self.emitter.get_temp_register()
        return_type = self.type_converter.get_node_type(node)
        return_llvm_type = self.__get_function_return_llvm_type(return_type)

        self.emitter.emit_line(f"  {result_reg} = call {return_llvm_type} @{mangled_name}({', '.join(arg_strs)})")
        return result_reg

    def load_field_from_this(self, field_name: str) -> str:
        field_ptr, field_llvm_type = self.__get_this_field_pointer(field_name)
        field_value = self.emitter.get_temp_register()
        self.emitter.emit_line(f"  {field_value} = load {field_llvm_type}, {field_llvm_type}* {field_ptr}")
        return field_value

    def store_field_to_this(self, field_name: str, value: str):
        field_ptr, field_llvm_type = self.__get_this_field_pointer(field_name)
        self.emitter.emit_line(f"  store {field_llvm_type} {value}, {field_llvm_type}* {field_ptr}")

    @staticmethod
    def get_llvm_type(data_type) -> str:
        return (data_type.to_llvm()
                if isinstance(data_type, DataType)
                else f"%struct.{data_type}*")

    def __get_this_field_pointer(self, field_name: str) -> tuple[str, str]:
        struct_name = self.current_struct_context
        fields = self.struct_ops.struct_definitions[struct_name]
        field_index = next(i for i, (name, _, _) in enumerate(fields) if name == field_name)
        field_llvm_type = fields[field_index][1]

        field_ptr = self.emitter.get_temp_register()
        self.emitter.emit_line(f"  {field_ptr} = getelementptr inbounds %struct.{struct_name}, "
                               f"%struct.{struct_name}* %this, i32 0, i32 {field_index}")
        return field_ptr, field_llvm_type

    def __prepare_function_context(self, func_name: str, return_type):
        self.function_return_types[func_name] = return_type
        self._saved_state = self.__save_state()
        self.__reset_for_function()
        self.in_function = True

    def __initialize_function_body(self, node, visitor, func_signature: str):
        self.__declare_function_params(node)
        node.body.accept(visitor)
        self.__store_function_definition(func_signature)

    def __build_function_signature(self, node) -> str:
        param_strs = [self.__build_param_string(p) for p in node.params]
        return_llvm_type = self.__get_return_type_for_signature(node.return_type)
        return f"define {return_llvm_type} @{node.variable}({', '.join(param_strs)}) {{"

    def __build_member_function_signature(self, struct_name: str, node, mangled_name: str) -> str:
        return_llvm_type = self.__get_llvm_type(node.return_type)
        param_strs = [f"%struct.{struct_name}* %this"] + [
            self.__build_param_string(p) for p in node.params]
        return f"define {return_llvm_type} @{mangled_name}({', '.join(param_strs)}) {{"

    def __build_param_string(self, param) -> str:
        llvm_type = self.__get_llvm_type(param.param_type)
        return f"{llvm_type} %{param.name}"

    def __declare_function_params(self, node):
        for param in node.params:
            var_type = (DataType.from_string(param.param_type)
                        if DataType.is_data_type(param.param_type)
                        else param.param_type)
            self.variable_registry.set_variable_type(param.name, var_type)
            self.variable_registry.set_variable_version(param.name, 0)

    def __store_function_definition(self, signature: str):
        lines = [signature] + self.emitter.translated_lines + ["}", ""]
        self.emitter.add_function_definition(lines)

    def __setup_this_context(self, struct_name: str):
        self.current_struct_context = struct_name
        for field_name, field_llvm_type, field_data_type in self.struct_ops.struct_definitions[struct_name]:
            field_type = (DataType.from_string(field_data_type)
                            if DataType.is_data_type(field_data_type)
                            else field_data_type)
            self.variable_registry.set_variable_type(field_name, field_type)
            self.variable_registry.set_variable_version(field_name, -1)

    def __build_call_argument(self, arg, visitor) -> str:
        arg_value = arg.accept(visitor)
        arg_type = self.type_converter.get_node_type(arg)
        arg_llvm_type = self.get_llvm_type(arg_type)
        return f"{arg_llvm_type} {arg_value}"

    def __save_state(self) -> dict:
        return {
            "emitter": self.emitter.copy_state(),
            "variable_registry": self.variable_registry.copy_state(),
            "in_function": self.in_function,}

    def __restore_state(self, state: dict):
        self.emitter.restore_state(state["emitter"])
        self.variable_registry.restore_state(state["variable_registry"])
        self.in_function = state["in_function"]

    def __reset_for_function(self):
        self.emitter.reset_for_function()
        self.variable_registry.reset()