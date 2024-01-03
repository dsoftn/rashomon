import commands_cls
from commands_cls import AbstractCommand


class Code():
    def __init__(self) -> None:
        # self.commands = [ command name, command class ]
        self.commands = [
            ["#", commands_cls.Cmd_Comment],
            ["Parent", commands_cls.Cmd_Parent],
            ["Index", commands_cls.Cmd_Index],
            ["BeginSegment", commands_cls.Cmd_BeginSegment],
            ["EndSegment", commands_cls.Cmd_EndSegment],
            ["DefineStartString", commands_cls.Cmd_DefineStartString],
            ["EndDefineStartString", commands_cls.Cmd_EndDefineStartString],
            ["DefineEndString", commands_cls.Cmd_DefineEndString],
            ["EndDefineEndString", commands_cls.Cmd_EndDefineEndString],
            ["MatchCase", commands_cls.Cmd_MatchCase],
            ["IsEqual", commands_cls.Cmd_IsEqual],
            ["StartsWith", commands_cls.Cmd_StartsWith],
            ["EndsWith", commands_cls.Cmd_EndsWith],
            ["If", commands_cls.Cmd_If],
            ["EndIf", commands_cls.Cmd_EndIf],
            ["StartString", commands_cls.Cmd_StartString],
            ["EndString", commands_cls.Cmd_EndString],
            ["ContainsString", commands_cls.Cmd_ContainsString]

        ]

    def is_string_meet_conditions(self, code: str, string: str, matchcase: bool = False) -> bool:
        abs_command_obj = AbstractCommand("", 0, "", "")
        error = []

        code_list_all = code.split("\n")
        code_list = []
        in_if_comm = False
        for line in code_list_all:
            line: str = line.lstrip()
            if line.startswith("If"):
                in_if_comm = True
            if in_if_comm:
                code_list.append(line)
            if line.startswith("EndIf"):
                in_if_comm = False
        if in_if_comm:
            error.append('Error. Missing "EndIf"')

        criteria_meet = True
        for line in code_list:
            line: str = line.lstrip()
            command_name = self.get_command_object_for_code_line(line, return_command_name_only=True)
            if command_name in abs_command_obj.COMMANDS_CONDITIONS:
                if not line.startswith("If"):
                    line = "If " + line
                command_obj: AbstractCommand = self.get_command_object_for_code_line(line)(line, 0, "", "")
                command_obj.execute()
                conditions = command_obj.data.Conditions
                if conditions is None:
                    continue
                if not conditions["valid"]:
                    error.append(f'Error in line "{line}"  ... Skipped.')
                    continue
                eval_text = conditions["eval_text"]
                for idx, item in enumerate(conditions["conditions"]):
                    condition_value = self._get_condition_value(item, string, matchcase=matchcase)
                    if condition_value is None:
                        error.append(f'Unrecognized condition "{item[0]}" = "{item[1]}" in line "{line}"  ... Set to "True" !')
                        condition_value = True
                    if condition_value:
                        eval_text = eval_text.replace(f"CON[{idx}]", "True")
                    else:
                        eval_text = eval_text.replace(f"CON[{idx}]", "False")
                eval_result = None
                if eval_text.strip():
                    try:
                        eval_result = eval(eval_text)
                    except Exception as e:
                        error.append(f'Command execute failed : "{line}"  ... Skipped !\nError: {e}')
                        continue
                else:
                    eval_result = True

                if eval_result is None or eval_result is False:
                    criteria_meet = False
                    break

        result = {
            "value": criteria_meet,
            "error": error
        }
        return result        

    def _get_condition_value(self, if_command_condition: list, text: str, matchcase: bool = False) -> bool:
        command: str = if_command_condition[0]
        argument: str = if_command_condition[1]
        if not matchcase:
            argument = argument.lower()
            text = text.lower()

        result = None
        if command.startswith("StartString"):
            result = text.startswith(argument)
        elif command.startswith("EndString"):
            result = text.endswith(argument)
        elif command.startswith("ContainsString"):
            if text.find(argument) == -1:
                result = False
            else:
                result = True

        return result
    
    def get_code_block(self, code: str, block_start: str, block_end: str) -> str:
        code_list = code.split("\n")
        block = ""
        in_block = False
        for line in code_list:
            if line.lstrip().startswith(block_start):
                in_block = True
            if in_block:
                block += line + "\n"
            if line.lstrip().startswith(block_end):
                in_block = False
        return block
    
    def is_command_syntax_valid(self, command_line: str) -> bool:
        command_line = command_line.lstrip()
        is_valid = None
        for command in self.commands:
            if command_line.startswith(command[0]):
                command_obj: AbstractCommand = command[1](command_line, 0, "", "")
                is_valid = command_obj.is_valid()
                break
        return is_valid
    
    def get_command_object_for_code_line(self, code_line: str, return_command_name_only: bool = False) -> str:
        code_line = code_line.strip()
        if code_line.startswith("Not"):
            code_line = code_line[3:].strip()

        for i in "()='\"":
            code_line = code_line.replace(i," ")
        pos = code_line.find(" ")
        if pos != -1:
            code_line = code_line[:pos]
        
        if code_line.startswith("Not"):
            code_line = code_line[3:].strip()
        
        for i in self.commands:
            if i[0] == code_line:
                if return_command_name_only:
                    return i[0]
                else:
                    return i[1]
        return None
    
    def get_command_value(self, command_line: str) -> str:
        result = None
        command_line = command_line.lstrip()

        for command in self.commands:
            if command_line.startswith(command[0]):
                command_obj: AbstractCommand = command[1](command_line, 0, "", "")
                result = command_obj.value()
                break
        return result

    def get_segment_command_value(self, segment_code: str, command: str, multi_results: bool = False) -> str:
        code_line = None
        command_values = []
        for idx, i in enumerate(segment_code.split("\n")):
            if i.lstrip().startswith(command):
                result = self._get_multi_values(i)
                for val in result:
                    command_values.append(val)

                code_line = idx

        if multi_results:
            return command_values

        if code_line is None:
            return None
        
        command_value = None
        command_obj: AbstractCommand = self._get_command_object(command)(segment_code, code_line, "", "")
        for i in segment_code.split("\n"):
            if command_obj.is_valid():
                command_value = command_obj.value()
        return command_value

    def _get_multi_values(self, command_line: str) -> list:
        result = []
        command_line = command_line.lstrip()
        in_container = False
        parameter = ""
        container_type = None
        abs_comm = AbstractCommand(command_line, 0, "", "")
        start_con = [x[0] for x in abs_comm.CONTAINERS]
        end_con = [x[1] for x in abs_comm.CONTAINERS]
        for i in command_line:
            if i in start_con and not in_container:
                in_container = True
                container_type = start_con.index(i)
                continue
            if i in end_con and in_container:
                if i == end_con[container_type]:
                    in_container = False
                    result.append(parameter)
                    parameter = ""
                    continue
            if in_container:
                parameter += i
        return result
    
    def _get_command_object(self, command_name: str) -> AbstractCommand:
        for command in self.commands:
            if command[0] == command_name:
                return command[1]
        return None
