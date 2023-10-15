import code_cls
from commands_cls import AbstractCommand


class Segment():
    def __init__(self, segment_script: str) -> None:
        self.segment_script = segment_script

        self.code_handler = code_cls.Code()

    def get_list_of_rules_for_GUI(self):
        rules_commands = [
            ["StartString", "If "],
            ["EndString", "If "],
            ["ContainsString", "If "],
            ["IsEqual", ""],
            ["StartsWith", ""],
            ["EndsWith", ""]
        ]
        
        start_block = self.code_handler.get_code_block(self.segment_script, "DefineStartString", "EndDefineStartString")
        end_block = self.code_handler.get_code_block(self.segment_script, "DefineEndString", "EndDefineEndString")
        rules = []
        
        script_list = start_block.split("\n")
        for line in script_list:
            command_obj: AbstractCommand = self.code_handler.get_command_object_for_code_line(line)
            if command_obj is not None:
                command_obj = command_obj(line, 0, "", "")
                for i in rules_commands:
                    if command_obj.data.Command == i[0]:
                        line = line.lstrip()
                        if line.startswith("If "):
                            line = line[3:]
                            line = line.lstrip()
                        rule = i[1] + line
                        rules.append("START: " + rule)
        script_list = end_block.split("\n")
        for line in script_list:
            command_obj: AbstractCommand = self.code_handler.get_command_object_for_code_line(line)
            if command_obj is not None:
                command_obj = command_obj(line, 0, "", "")
                for i in rules_commands:
                    if command_obj.data.Command == i[0]:
                        line = line.lstrip()
                        if line.startswith("If "):
                            line = line[3:]
                            line = line.lstrip()
                        rule = i[1] + line
                        rules.append("END: " + rule)
        return rules
    
    def execute(self, text: str) -> dict:
        code_result = {
            "executed": False,
            "error": [],
            "start": {
                "DefineStartString": self.code_handler.get_code_block(self.segment_script, "DefineStartString", "EndDefineStartString"),
                "IsEqual": [],
                "StartsWith": [],
                "EndsWith": [],
                "conditions": []
            },
            "end": {
                "DefineEndString": self.code_handler.get_code_block(self.segment_script, "DefineEndString", "EndDefineEndString"),
                "IsEqual": [],
                "StartsWith": [],
                "EndsWith": [],
                "conditions": []
            },
            "selections": {}
        }
        
        code_result["start"]["IsEqual"] = self.code_handler.get_segment_command_value(code_result["start"]["DefineStartString"], "IsEqual", multi_results=True)
        code_result["start"]["StartsWith"] = self.code_handler.get_segment_command_value(code_result["start"]["DefineStartString"], "StartsWith", multi_results=True)
        code_result["start"]["EndsWith"] = self.code_handler.get_segment_command_value(code_result["start"]["DefineStartString"], "EndsWith", multi_results=True)

        code_result["end"]["IsEqual"] = self.code_handler.get_segment_command_value(code_result["end"]["DefineEndString"], "IsEqual", multi_results=True)
        code_result["end"]["StartsWith"] = self.code_handler.get_segment_command_value(code_result["end"]["DefineEndString"], "StartsWith", multi_results=True)
        code_result["end"]["EndsWith"] = self.code_handler.get_segment_command_value(code_result["end"]["DefineEndString"], "EndsWith", multi_results=True)

        # Check if main conditions are valid
        error_msg = "The START selection has the value 'IsEqual' set, but the string with which this value should start or end conflicts with this value."

        if code_result["start"]["DefineStartString"] and (not (code_result["start"]["IsEqual"] or (code_result["start"]["StartsWith"] and code_result["start"]["EndsWith"]))):
            error_msg = 'The start of the selection is not properly defined.\nYou must define the "IsEqual" field or the "StartsWith" and "EndsWith" fields.'
            code_result["error"].append(error_msg)

        if code_result["end"]["DefineEndString"] and (not (code_result["end"]["IsEqual"] or (code_result["end"]["StartsWith"] and code_result["end"]["EndsWith"]))):
            error_msg = 'The end of the selection is not properly defined.\nYou must define the "IsEqual" field or the "StartsWith" and "EndsWith" fields.'
            code_result["error"].append(error_msg)

        if code_result["error"]:
            code_result["error"].append("Code execution was interrupted due to an error.")
            return code_result
        
        # Check for case sensitivity
        match_case = self.code_handler.get_segment_command_value(self.segment_script, "MatchCase")
        if match_case is None:
            match_case = False
        if match_case:
            txt = text
        else:
            txt = text.lower()
            code_result["start"]["IsEqual"] = self._lower_list(code_result["start"]["IsEqual"])
            code_result["start"]["StartsWith"] = self._lower_list(code_result["start"]["StartsWith"])
            code_result["start"]["EndsWith"] = self._lower_list(code_result["start"]["EndsWith"])
            code_result["end"]["IsEqual"] = self._lower_list(code_result["end"]["IsEqual"])
            code_result["end"]["StartsWith"] = self._lower_list(code_result["end"]["StartsWith"])
            code_result["end"]["EndsWith"] = self._lower_list(code_result["end"]["EndsWith"])

        # Find all start strings
        occurrences = []
        pos = 0
        while code_result["start"]["DefineStartString"]:
            if code_result["start"]["IsEqual"]:
                pos, found_item = self._find_first_pos(code_result["start"]["IsEqual"], txt, pos)
                if pos == -1:
                    break
                occurrences.append([pos, pos + len(found_item), found_item])
                pos += len(found_item)
                continue

            pos, found_item_start = self._find_first_pos(code_result["start"]["StartsWith"], txt, pos)
            pos_end, found_item_end = self._find_first_pos(code_result["start"]["EndsWith"], txt, pos + len(found_item_start))
            if pos == -1 or pos_end == -1:
                break
            
            occurrences.append([pos, pos_end + len(found_item_end), txt[pos:pos_end + len(found_item_end)]])
            pos = pos_end + len(found_item_end)

        delete_occur = []
        for idx, item in enumerate(occurrences):
            is_valid = self.code_handler.is_string_meet_conditions(code_result["start"]["DefineStartString"], item[2], matchcase=match_case)
            
            for i in is_valid["error"]:
                code_result["error"].append(i)

            if not is_valid["value"]:
                delete_occur.insert(0, idx)

        for idx in delete_occur:
            occurrences.pop(idx)

        # Case when DefineStartString does not exist:
        if not code_result["start"]["DefineStartString"]:
            occurrences = [[0, 0, ""]]
        
        # Find all End Strings
        count = 0
        for occurrence in occurrences:
            pos = occurrence[1]
            
            found_end = False
            end_selection = None
            while code_result["end"]["DefineEndString"]:
                if code_result["end"]["IsEqual"]:
                    pos, found_item = self._find_first_pos(code_result["end"]["IsEqual"], txt, pos)
                    if pos == -1:
                        break
                    end_selection = [pos, pos + len(found_item), found_item]
                    pos += len(found_item)
                else:
                    pos, found_item_start = self._find_first_pos(code_result["end"]["StartsWith"], txt, pos)
                    pos_end, found_item_end = self._find_first_pos(code_result["end"]["EndsWith"], pos + len(found_item_start))
                    if pos == -1 or pos_end == -1:
                        break
                    end_selection = [pos, pos_end + len(found_item_end), txt[pos:pos_end + len(found_item_end)]]
                    pos += len(found_item_start)
                
                is_valid = self.code_handler.is_string_meet_conditions(code_result["end"]["DefineEndString"], end_selection[2])
                
                for i in is_valid["error"]:
                    code_result["error"].append(i)

                if is_valid["value"]:
                    found_end = end_selection
                    break
            
            # Case when DefineEndString does not exist
            if not code_result["end"]["DefineEndString"]:
                found_end = [len(txt), len(txt), ""]

            if found_end:
                code_result["selections"][count] = {
                    "start": occurrence[1],
                    "end": found_end[0],
                    "selection": text[occurrence[1]:found_end[0]]
                }
                count += 1
            
        return code_result

    def _find_first_pos(self, items: list, text: str, from_pos: int) -> tuple:
        """Find the first position of any item in items in text from from_pos."""
        result = len(text) + 1
        found_item = ""
        for item in items:
            pos = text.find(item, from_pos)
            if pos != -1 and pos < result:
                result = pos
                found_item = item
                
        if result > len(text):
            result = -1
        return (result, found_item)

    def _lower_list(self, list_to_lower: list) -> list:
        result = []
        for i in range(len(list_to_lower)):
            result.append(list_to_lower[i].lower())
        return result

    @property
    def parent(self) -> str:
        return self.code_handler.get_segment_command_value(self.segment_script, "Parent")

    @property
    def name(self) -> str:
        return self.code_handler.get_segment_command_value(self.segment_script, "BeginSegment")

    @property
    def code(self) -> str:
        return self.segment_script

    @property
    def index(self) -> str:
        return self.code_handler.get_segment_command_value(self.segment_script, "Index")

