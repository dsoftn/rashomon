class Data():
    COLOR_COMMENT = "#aaff7f"
    COLOR_BLOCK = "#007e00"
    COLOR_KEYWORD = "#d4ff82"
    COLOR_CONDITION = "#66ce99"
    COLOR_OPERATOR = "#ff557f"
    COLOR_CONTAINER = "#aa5500"
    COLOR_STRING = "#bdb7ff"

    EXTRA_COLOR_RULES = [
        ["If", "#c8c896"],
        ["EndIf", "#c8c896"],
        ["BeginSegment", "#0055ff"],
        ["EndSegment", "#0055ff"]
    ]

    def __init__(self) -> None:
        self.CommandLineText = None
        self.CommandLineNumber = None
        self.Code = None

        self.Command = None
        self.Description = None
        self.Example = None
        self.Not = None
        self.CommandType = None
        self.Argument = None
        self.Conditions = None

        self.Valid = None
        self.Value = None
        self.Segment = None
        self.Text = None
        self.Selection = None

        self.AutoCompleteLine = None
        self.AutoCompleteCursorPosition = None
        self.ColorMap = None

class AbstractCommand():
    CONTAINERS = [
        ['"', '"', '"'],
        ["'", "'", "'"],
        ["|", "|", "|"],
        ["`", "`", "`"]
    ]
    BLOCK = 0
    KEYWORD = 1
    COMMENT = 2
    CONDITION = 3
    OPERATOR = 4

    COMMANDS_CONDITIONS = [
        "StartString",
        "EndString",
        "ContainsString",
        "If"
        ]
    COMMANDS_OPERATOR = [
        "And",
        "Or",
        "Not"
    ]
    COMMANDS_BLOCK = [
        "BeginSegment",
        "EndSegment",
        "DefineStartString",
        "EndDefineStartString",
        "DefineEndString",
        "EndDefineEndString",
        "If",
        "EndIf"
    ]
    COMMANDS_KEYWORD = [
        "Parent",
        "Index",
        "MatchCase",
        "IsEqual",
        "StartsWith",
        "EndsWith"
    ]

    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self._command_line: str = code.split("\n")[line_number]
        self._code = code
        self._line_number = line_number
        self._text = text
        self._selection = selection

        self.data = Data()

    def is_valid(self):
        raise NotImplementedError("Error. Function has not been implemented yet.")
    
    def value(self):
        raise NotImplementedError("Error. Function has not been implemented yet.")

    def selection(self):
        raise NotImplementedError("Error. Function has not been implemented yet.")

    def execute(self):
        raise NotImplementedError("Error. Function has not been implemented yet.")
    
    def _has_container(self, command_text: str) -> bool:
        txt = command_text
        delimiters = self.CONTAINERS
        
        in_container = False
        found_container = False
        start_delim = [x[0] for x in delimiters]
        end_delim = [x[1] for x in delimiters]
        container_type = None
        for char in txt:
            if char in start_delim and not in_container:
                container_type = start_delim.index(char)
                in_container = True
                continue
            
            if not in_container:
                continue

            if char == end_delim[container_type]:
                found_container = True
                break
            
        if found_container:
            return True
        else:
            return False

    def _get_simple_value(self, txt: str) -> str:
        pos = txt.find("=")
        if pos == -1:
            return None
        
        result = txt[pos:].strip()
        return result
    
    def _text_in_container(self, txt: str, delimiter: str = None) -> str:
        if delimiter:
            if isinstance(delimiter, str):
                for i in self.CONTAINERS:
                    if i[2] == delimiter:
                        delimiters = [i]
                        break
                else:
                    delimiters_list = ", ".join([x[2] for x in self.CONTAINERS])
                    raise ValueError(f"Unknown delimiter: {delimiter}   Allowed delimiters are : {delimiters_list}")
            elif isinstance(delimiter, list) or isinstance(delimiter, tuple):
                delimiters = delimiter
            else:
                raise ValueError(f"Unknown delimiter: {delimiter}   Custom delimiter must be list or tuple. ['start', 'end', 'name']")
        else:
            delimiters = self.CONTAINERS
        
        result = ""
        in_container = False
        found_container = False
        start_delim = [x[0] for x in delimiters]
        end_delim = [x[1] for x in delimiters]
        container_type = None
        for char in txt:
            if char in start_delim and not in_container:
                container_type = start_delim.index(char)
                in_container = True
                continue
            
            if not in_container:
                continue

            if char == end_delim[container_type]:
                found_container = True
                break
            
            if in_container:
                result += char

        if found_container:
            return result
        else:
            return None

    def _get_if_conditions(self, if_command: str) -> dict:
        if_command = if_command.lstrip()
        if_resolved = {
            "valid": False,
            "command_line": if_command,
            "conditions": None,
            "eval_text": None
        }
        if not if_command.startswith("If"):
            return if_resolved
        
        delimiters = self.CONTAINERS
        start_delim = [x[0] for x in delimiters]
        end_delim = [x[1] for x in delimiters]
        container_type = None
        
        conditions = []
        txt = f" {if_command[3:]} "
        txt_con = ""
        container_content = ""
        command = ""
        pos = 0
        is_if_valid = True
        negative_command = False
        in_container = False
        prev_command = None
        while True:
            if pos >= len(txt):
                break

            i = txt[pos]

            if i in start_delim and not in_container:
                container_type = start_delim.index(i)
                in_container = True
                pos += 1
                continue
            if in_container:
                if i == end_delim[container_type]:
                    in_container = False
                    if not command:
                        if prev_command:
                            command = prev_command
                        else:
                            is_if_valid = False
                            break
                    else:
                        prev_command = command

                    conditions.append([command, container_content, negative_command])
                    negative_command = False
                    container_content = ""
                    command = ""
                    txt_con += f" CON[{len(conditions)-1}] "
                    pos += 1
                    continue
                else:
                    container_content += i
                    pos += 1
                    continue

            if i in " =":
                if not command:
                    pos += 1
                    continue

                if command.capitalize() in self.COMMANDS_OPERATOR:
                    if command.lower() == "not":
                        negative_command = True
                    txt_con += f" {command.lower()} "
                    pos += 1
                    command = ""
                    continue

            if i in "() ":
                txt_con += i
                pos += 1
                continue

            command += i
            command = command.strip(" =")
            pos += 1

        if in_container:
            is_if_valid = False
        
        for i in self.COMMANDS_CONDITIONS:
            txt_con = txt_con.replace(i, " ")
        
        if_resolved["valid"] = is_if_valid
        if_resolved["command_line"] = if_command
        if_resolved["conditions"] = conditions
        if_resolved["eval_text"] = txt_con

        return if_resolved

    def _is_if_condition_syntax_valid(self, if_command: str) -> bool:
        if_command = if_command.lstrip()
        result = self._get_if_conditions(if_command=if_command)
        if result["valid"]:
            return True
        else:
            return False

    def _get_segment_name(self) -> str:
        txt_list = self._code.split("\n")
        pos = self._line_number
        if pos >= len(txt_list):
            return None
        
        while pos >= 0:
            if txt_list[pos].startswith("BeginSegment"):
                if self._has_container(txt_list[pos]):
                    return self._text_in_container(txt_list[pos])
                else:
                    return None
            pos -= 1
        return None

    def _get_color_map_for_simple_command(self) -> list:
        delimiters = self.CONTAINERS
        
        result = []
        in_container = False
        found_container = None
        start_delim = [x[0] for x in delimiters]
        end_delim = [x[1] for x in delimiters]
        container_type = None
        pos = 0
        old_pos = 0
        txt = self._command_line + " "
        command = ""
        invalid_command_color = "#b4b4b4"
        found_command = False
        operators_lower = [x.lower() for x in self.COMMANDS_OPERATOR]
        commands_list = [
            [self.COMMANDS_CONDITIONS, self.data.COLOR_CONDITION],
            [self.COMMANDS_KEYWORD, self.data.COLOR_KEYWORD],
            [self.COMMANDS_BLOCK, self.data.COLOR_BLOCK],
            [self.COMMANDS_OPERATOR, self.data.COLOR_OPERATOR],
            [operators_lower, self.data.COLOR_OPERATOR]
        ]
        
        while True:
            if pos >= len(txt):
                break

            char = txt[pos]

            if char in start_delim and not in_container:
                container_type = start_delim.index(char)
                found_container = pos
                in_container = True
                pos += 1
                continue
            
            if in_container and char == end_delim[container_type]:
                result.append([found_container, found_container+1, self.data.COLOR_CONTAINER])
                result.append([found_container+1, pos, self.data.COLOR_STRING])
                result.append([pos, pos+1, self.data.COLOR_CONTAINER])
                found_container = None
                in_container = False
                pos += 1
                old_pos = pos
                continue

            if in_container:
                pos += 1
                continue

            if char in "()= \n\t" and command.strip():
                for item in self.data.EXTRA_COLOR_RULES:
                    if command.strip() == item[0]:
                        result.append([old_pos, pos, item[1]])
                        old_pos = pos
                        found_command = True
                        break

                if not found_command:
                    for item in commands_list:
                        for i in item[0]:
                            if command.strip() == i:
                                result.append([old_pos, pos, item[1]])
                                found_command = True
                                old_pos = pos
                if not found_command:
                    result.append([old_pos, pos, invalid_command_color])
                    old_pos = pos
                else:
                    found_command = False
                command = ""

            if char in "()=":
                result.append([old_pos, pos + 1, self.data.COLOR_CONTAINER])
                pos += 1
                old_pos = pos
                continue

            command += char
            pos += 1

        return result

    def _keyword_is_equal_to(self):
        txt = self._command_line.lstrip()
        pos = txt.find("=")
        if pos == -1:
            if len(txt) > len(self.data.Command):
                txt = " " + txt[len(self.data.Command):]
                pos = 0
        
        txt = txt[pos+1:].strip()
        if txt:
            for i in self.CONTAINERS:
                if txt[0] == i[0]:
                    txt = txt.strip(i[0])
                    break
        
        return txt


class Cmd_Comment(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "#"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'This is a comment. Anything in a line of code starting with "#" will be ignored.'
        self.data.Example = ""
        self.data.CommandType = self.COMMENT
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = self.is_valid()
        self.data.Value = self.value()
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = "# "
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine)
        self.data.ColorMap = [0, len(self.command_line), self.data.COLOR_COMMENT]

    def is_valid(self):
        if self.command_line.lstrip().startswith(self.name):
            return True
        else:
            return False

    def value(self):
        return None

    def selection(self):
        return self.data.Selection

    def execute(self):
        return self.data


class Cmd_Parent(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "Parent"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'Sets the parent segment.\nEach segment processes only the part of the text it receives from the parent.'
        self.data.Example = 'Parent = "Some_segment_name"'
        self.data.CommandType = self.KEYWORD
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'Parent = ""'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine) - 1
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True
            value = self._keyword_is_equal_to()

        self.data.Valid = is_valid
        self.data.Argument = value
        if value == "None":
            value = None
        self.data.Value = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_Index(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "Index"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'The text index that the segment will receive from the parent.\nWhen the parent segment executes its code, it often receives as a result several text selections.\nThis index indicates the sequence number of the selection.\nIndices start at 0.'
        self.data.Example = 'Index = 0'
        self.data.CommandType = self.KEYWORD
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'Index = ""'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine) - 1
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True
            value = self._keyword_is_equal_to()

        self.data.Valid = is_valid
        self.data.Argument = value
        try:
            value_int = int(value)
        except:
            value_int = None
        self.data.Value = value_int
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_BeginSegment(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "BeginSegment"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'It marks the beginning of the segment and determines its name.\nEverything between the "BeginSegment" and "EndSegment" commands is part of the segment.'
        self.data.Example = 'BeginSegment (Segment_Name)\nEndSegment'
        self.data.CommandType = self.BLOCK
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'BeginSegment ()'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine) - 1
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True
            containers = [x for x in self.CONTAINERS]
            containers.append(["(", ")", "()"])
            value = self._text_in_container(self.data.CommandLineText, containers)

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_EndSegment(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "EndSegment"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'It marks the end of the segment and determines its name.\nEverything between the "BeginSegment" and "EndSegment" commands is part of the segment.'
        self.data.Example = 'BeginSegment (Segment_Name)\nEndSegment'
        self.data.CommandType = self.BLOCK
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'EndSegment'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine)
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_DefineStartString(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "DefineStartString"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'It marks the beginning of the code block in which the string from which the text selection begins is defined.\nEach segment must contain the definition of the string from which the text selection begins,\nas well as the definition of the string up to which the text is selected.'
        self.data.Example = 'DefineStartString\nEndDefineStartString'
        self.data.CommandType = self.BLOCK
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'DefineStartString'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine)
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_EndDefineStartString(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "EndDefineStartString"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'It marks the end of the code block in which the string from which the text selection begins is defined.\nEach segment must contain the definition of the string from which the text selection begins,\nas well as the definition of the string up to which the text is selected.'
        self.data.Example = 'DefineStartString\nEndDefineStartString'
        self.data.CommandType = self.BLOCK
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'EndDefineStartString'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine)
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_DefineEndString(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "DefineEndString"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'It marks the beginning of the code block in which the string up to which the text will be selected is defined.\nEach segment must contain the definition of the string from which the text selection starts,\nalso the definition of the string up to which the text is selected.'
        self.data.Example = 'DefineEndString\nEndDefineEndString'
        self.data.CommandType = self.BLOCK
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'DefineEndString'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine)
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_EndDefineEndString(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "EndDefineEndString"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'It marks the end of the code block in which the string up to which the text will be selected is defined.\nEach segment must contain the definition of the string from which the text selection starts,\nalso the definition of the string up to which the text is selected.'
        self.data.Example = 'DefineEndString\nEndDefineEndString'
        self.data.CommandType = self.BLOCK
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'EndDefineEndString'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine)
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_MatchCase(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "MatchCase"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'Indicates whether upper and lower case letters will be taken into account when defining the strings between which the selected text is located.\nIt can have the values ​​True or False.'
        self.data.Example = 'MatchCase = False'
        self.data.CommandType = self.KEYWORD
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'MatchCase = '
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine)
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True
            value = self._keyword_is_equal_to()

        self.data.Valid = is_valid
        if value:
            if value.lower() == "true":
                self.data.Value = True
            elif value.lower() == "false":
                self.data.Value = False
        else:
            self.data.Value = None
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_IsEqual(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "IsEqual"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'Defines the starting or ending string between which the selected text is located.\nThe string must be equal to the value of this command in order for the condition to be satisfied.'
        self.data.Example = 'IsEqual "Some_Expression"'
        if self.command_line.lstrip().startswith("Not"):
            self.data.Not = True
        else:
            self.data.Not = False
        self.data.CommandType = self.KEYWORD
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'IsEqual ""'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine) - 1
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True
            value = self._text_in_container(self.data.CommandLineText)

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_StartsWith(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "StartsWith"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'Defines the starting or ending string between which the selected text is located.\nThe string must start with the value of this command in order for the condition to be satisfied.'
        self.data.Example = 'StartsWith "Some_Expression"'
        if self.command_line.lstrip().startswith("Not"):
            self.data.Not = True
        else:
            self.data.Not = False
        self.data.CommandType = self.KEYWORD
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'StartsWith ""'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine) - 1
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True
            value = self._text_in_container(self.data.CommandLineText)

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_EndsWith(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "EndsWith"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'Defines the starting or ending string between which the selected text is located.\nThe string must end with the value of this command in order for the condition to be satisfied.'
        self.data.Example = 'EndsWith "Some_Expression"'
        if self.command_line.lstrip().startswith("Not"):
            self.data.Not = True
        else:
            self.data.Not = False
        self.data.CommandType = self.KEYWORD
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'EndsWith ""'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine) - 1
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True
            value = self._text_in_container(self.data.CommandLineText)

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_If(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "If"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'Block "If" - "EndIf"\nThe conditions under which the start/end string will be accepted are defined within this block.'
        self.data.Example = 'If\nContainsString "Expression" or ContainsString "Expression2"\nEndIf'
        self.data.CommandType = self.BLOCK
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'If '
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine)
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        self.data.Conditions = None
        is_valid = self._is_if_condition_syntax_valid(self.data.CommandLineText)
        value = None
        if is_valid:
            self.data.Conditions = self._get_if_conditions(self.data.CommandLineText)

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_EndIf(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "EndIf"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'Block "If" - "EndIf"\nThe conditions under which the start/end string will be accepted are defined within this block.'
        self.data.Example = 'If\nContainsString "Expression" or ContainsString "Expression2"\nEndIf'
        self.data.CommandType = self.BLOCK
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'EndIf'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine)
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip().startswith(self.name):
            is_valid = True

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_StartString(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "StartString"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'Defines the starting or ending string between which the selected text is located.\nThe string must start with the value of this command in order for the condition to be satisfied.\nYou can use multiple "StartString", "EndString" and "ContainsString" commands in one line of code.\nEach command must be separated by a logical operator "And" or "Or".\nThe "Not" operator is used if it is necessary that the command does not satisfy condition.'
        self.data.Example = 'StartString "Expression1" And EndString "Expression2" Or ContainsString "Expression3"'
        if self.command_line.lstrip().startswith("Not"):
            self.data.Not = True
        else:
            self.data.Not = False
        self.data.CommandType = self.KEYWORD
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'StartString ""'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine) - 1
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip(" Not").startswith(self.name):
            is_valid = True
            value = self._text_in_container(self.data.CommandLineText)

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_EndString(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "EndString"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'Defines the starting or ending string between which the selected text is located.\nThe string must end with the value of this command in order for the condition to be satisfied.\nYou can use multiple "StartString", "EndString" and "ContainsString" commands in one line of code.\nEach command must be separated by a logical operator "And" or "Or".\nThe "Not" operator is used if it is necessary that the command does not satisfy condition.'
        self.data.Example = 'StartString "Expression1" And EndString "Expression2" Or ContainsString "Expression3"'
        if self.command_line.lstrip().startswith("Not"):
            self.data.Not = True
        else:
            self.data.Not = False
        self.data.CommandType = self.KEYWORD
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'EndString ""'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine) - 1
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip(" Not").startswith(self.name):
            is_valid = True
            value = self._text_in_container(self.data.CommandLineText)

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data


class Cmd_ContainsString(AbstractCommand):
    def __init__(self, code: str, line_number: int, text: str, selection: str) -> None:
        self.name = "ContainsString"
        super().__init__(code, line_number, text, selection)

        self.command_line: str = code.split("\n")[line_number]

        self.data.CommandLineText = self.command_line
        self.data.CommandLineNumber = line_number
        self.data.Code = code

        self.data.Command = self.name
        self.data.Description = 'Defines the starting or ending string between which the selected text is located.\nThe string must contain value of this command in order for the condition to be satisfied.\nYou can use multiple "StartString", "EndString" and "ContainsString" commands in one line of code.\nEach command must be separated by a logical operator "And" or "Or".\nThe "Not" operator is used if it is necessary that the command does not satisfy condition.'
        self.data.Example = 'StartString "Expression1" And EndString "Expression2" Or ContainsString "Expression3"'
        if self.command_line.lstrip().startswith("Not"):
            self.data.Not = True
        else:
            self.data.Not = False
        self.data.CommandType = self.KEYWORD
        self.data.Argument = None
        self.data.Conditions = None
        
        self.data.Valid = None
        self.data.Value = None
        self.data.Segment = self._get_segment_name()
        self.data.Text = text
        self.data.Selection = selection

        self.data.AutoCompleteLine = 'ContainsString ""'
        self.data.AutoCompleteCursorPosition = len(self.data.AutoCompleteLine) - 1
        self.data.ColorMap = self._get_color_map_for_simple_command()

    def is_valid(self):
        self.execute()
        return self.data.Valid

    def value(self):
        self.execute()
        return self.data.Value

    def selection(self):
        self.execute()
        return self.data.Selection

    def execute(self):
        is_valid = False
        value = None
        if self.command_line.lstrip(" Not").startswith(self.name):
            is_valid = True
            value = self._text_in_container(self.data.CommandLineText)

        self.data.Valid = is_valid
        self.data.Value = value
        self.data.Argument = value
        self.data.Conditions = None
        # self.data.Selection = self.data.Selection
            
        return self.data
