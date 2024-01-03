from segment_cls import Segment
import code_cls


class Script():
    def __init__(self, data_source: dict = None) -> None:
        if data_source is None:
            self.data_source = self._empty_data_source_dict()
        else:
            self.data_source = data_source

        self.code = code_cls.Code()

    def _empty_data_source_dict(self) -> dict:
        result = {
            "project": None,
            "selected": None,
            "type": None,
            "source": None,
            "text": None,
            "formated_text": None,
            "code": None
        }
        return result

    def segment(self, segment_name: str) -> Segment:
        segment_script = self._get_segment_script(segment_name=segment_name)
        return Segment(segment_script=segment_script)

    def load_data_source(self, data_source: dict) -> None:
        self.data_source = data_source

    def get_top_segment_names(self) -> list:
        top_segments = []
        segments = self.get_all_segments()
        for segment in segments:
            if segment.parent == "None" or segment.parent is None:
                top_segments.append(segment.name)
        return top_segments

    def get_segment_children(self, segment_name: str, names_only: bool = False) -> list:
        if names_only:
            return self._children_names_for_parent(segment_name)
        
        segments = self.get_all_segments()
        result = []
        for segment in segments:
            if segment.parent == segment_name:
                result.append(segment)
        return result

    def _children_names_for_parent(self, parent_name: str) -> list:
        code_list = self.data_source["code"].split("\n")
        result = []
        in_segment = False
        segment_name = ""
        seg_parent = ""
        for line in code_list:
            if line.lstrip().startswith("BeginSegment"):
                seg_parent = ""
                segment_name = ""
                segment_name = self.code.get_command_value(line)
                in_segment = True
            
            if line.lstrip().startswith("Parent") and in_segment:
                seg_parent = self.code.get_command_value(line)
            
            if line.lstrip().startswith("EndSegment") and in_segment:
                if segment_name and seg_parent:
                    if seg_parent == parent_name:
                        result.append(segment_name)
                seg_parent = ""
                segment_name = ""
                in_segment = False

        return result

    def update_block_in_segment(self, segment_name: str, new_block: str, replace_in_all_siblings: bool = False, feedback_function = None) -> str:
        original_segment = Segment(self._get_segment_script(segment_name=segment_name))

        segments_map = self.get_segments_map_name_parent()
        errors = ""
        count_segments = 0
        count = 0
        original_segment_parent = original_segment.parent
        sibling_segments = [x[0] for x in segments_map if x[1] == original_segment_parent]

        if replace_in_all_siblings:
            for segment in sibling_segments:
                self.delete_segment_children(segment, segments_map)

            for segment in sibling_segments:
                result = self._update_block_in_segment(segment_name=segment, new_block=new_block)
                count_segments += len(result["selections"])
                if result["error"]:
                    errors += "SEGMENT: " + segment + "\n"
                    errors += "\n".join(result["error"])
                    errors += "\n"*3
                count += 1
                if feedback_function:
                    is_aborted = feedback_function({"current": count, "total": len(sibling_segments)})
                    if is_aborted:
                        errors += "Interupted by User !\n"
                        return {"errors": errors, "count": count_segments}

        else:
            self.delete_segment_children(segment_name, segments_map)
            result = self._update_block_in_segment(segment_name=segment_name, new_block=new_block)
            count_segments += len(result["selections"])
            if result["error"]:
                errors += "SEGMENT: " + segment_name + "\n"
                errors += "\n".join(result["error"])
                errors += "\n"*3
        return {"errors": errors, "count": count_segments}

    def _update_block_in_segment(self, segment_name: str, new_block: str) -> list:
        new_block_list = new_block.split("\n")
        block_start = new_block_list[0].lstrip()
        block_end = new_block_list[-1].lstrip()

        segment = Segment(self._get_segment_script(segment_name))
        segment_code_list = segment.code.split("\n")
        segment_code_list_clean = []
        in_block = False
        for line in segment_code_list:
            if line.lstrip().startswith(block_start):
                in_block = True

            if line.lstrip().startswith(block_end):
                in_block = False
                if not block_end.startswith("EndSegment"):
                    continue

            if in_block:
                continue
            
            if line.lstrip().startswith("EndSegment"):
                segment_code_list_clean.append(new_block)
                if block_end.startswith("EndSegment"):
                    continue

            segment_code_list_clean.append(line)
        
        segment_code = "\n".join(segment_code_list_clean) + "\n"

        code_list = self.data_source["code"].split("\n")
        new_code = ""
        in_segment = False
        for line in code_list:
            if line.lstrip().startswith("BeginSegment"):
                if self.code.get_command_value(line) == segment_name:
                    in_segment = True
                
            if line.lstrip().startswith("EndSegment") and in_segment:
                in_segment = False
                continue

            if in_segment:
                continue

            new_code += line + "\n"
        
        new_code += segment_code

        self.data_source["code"] = new_code

        if self.data_source["formated_text"]:
            txt = self.data_source["formated_text"]
        else:
            txt = self.data_source["text"]

        segment = Segment(self._get_segment_script(segment_name=segment_name))
        text_dict = self.get_segment_text(segment_name=segment_name)
        short_text = txt[text_dict["start"]:text_dict["end"]]

        result = segment.execute(short_text)
        for index in result["selections"]:
            if result["selections"][index]["end"] <= result["selections"][index]["start"]:
                continue

            new_name = segment.name + "_" + self._add_leading_zeros(index)
            new_segment_code = f"""
BeginSegment ({new_name})
    Parent = "{segment_name}"
    Index = {int(index)}
EndSegment
"""
            new_code += new_segment_code + "\n"
        
        while True:
            new_code = new_code.replace("\n\n\n", "\n\n")
            if new_code.find("\n\n\n") == -1:
                break

        self.data_source["code"] = new_code
        return result

    def _add_leading_zeros(self, number: int, string_len: int = 3) -> str:
        txt = str(number)
        if len(txt) < string_len:
            txt = "0" * (string_len - len(txt)) + txt
        return txt

    def delete_segment_children(self, segment_name: str, segments_map: list = None, delete_current_segment_also: bool = False):
        if segments_map is None:
            segments_map = self.get_segments_map_name_parent()

        code_list = self.data_source["code"].split("\n")

        segements_to_delete = []

        self._segment_tree(segment_name=segment_name, tree_list=segements_to_delete, segments_map=segments_map)
        if delete_current_segment_also:
            segements_to_delete.append(segment_name)

        new_code = ""
        in_segment = False
        for line in code_list:
            if line.lstrip().startswith("BeginSegment"):
                name = self.code.get_command_value(line)
                if name in segements_to_delete:
                    in_segment = True

            if line.lstrip().startswith("EndSegment") and in_segment:
                in_segment = False
                continue
            if in_segment:
                continue
            new_code += line + "\n"
        while True:
            new_code = new_code.replace("\n\n\n", "\n\n")
            if new_code.find("\n\n\n") == -1:
                break
        self.data_source["code"] = new_code
        
    def _segment_tree(self, segment_name: str, tree_list: list, segments_map: list):
        children = [x[0] for x in segments_map if x[1] == segment_name]
        if children:
            for child in children:
                tree_list.append(child)
                self._segment_tree(child, tree_list=tree_list, segments_map=segments_map)
        return tree_list
    
    def get_segment_text(self, segment_name: str) -> dict:
        if segment_name not in self.get_all_segments(names_only=True):
            return None
        
        if self.data_source["formated_text"]:
            txt = self.data_source["formated_text"]
        else:
            txt = self.data_source["text"]

        segment_hierarchy = []
        seg_name = segment_name
        seg_index = None
        while True:
            segment = Segment(self._get_segment_script(segment_name=seg_name))
            segment_hierarchy.insert(0, [segment, seg_index])

            seg_index = segment.index
            if segment.parent is None:
                break
            seg_name = segment.parent
        
        segment_hierarchy.pop(len(segment_hierarchy)-1)
        text_start = 0
        text_end = len(txt)
        for segment in segment_hierarchy:
            segment_obj: Segment = segment[0]
            segment_index: int = segment[1]

            selections = segment_obj.execute(txt[text_start:text_end])["selections"]
            new_text_start = None
            new_text_end = None
            for selection in selections:
                if int(selection) == int(segment_index):
                    new_text_start = selections[selection]["start"]
                    new_text_end = selections[selection]["end"]
                    break
            if new_text_start is None:
                new_text_start = 0
            if new_text_end is None:
                new_text_end = 0

            text_start += new_text_start
            text_end = text_start + (new_text_end - new_text_start)
        
        result = {
            "start": text_start,
            "end": text_end
        }
        return result

    def rename_segment(self, segment_to_rename: str, new_name: str) -> dict:
        code_list = [x for x in self.data_source["code"].split("\n")]
        
        result = {
            "renamed": 0,
            "parent_changed": 0,
            "error": None
        }

        if new_name in self.get_all_segments(names_only=True):
            result["error"] = f'Error.\nSegment name "{new_name}" already exist.\nName cannot be changed!'
            return result
        elif not new_name:
            result["error"] = 'Error.\nNew segment name is not defined.\nName cannot be changed!'
            return result
        elif not segment_to_rename:
            result["error"] = 'Error.\nCurrent segment is not defined.\nName cannot be changed!'
            return result

        for i, line in enumerate(code_list):
            if line.lstrip().startswith("BeginSegment"):
                segment_name = self.code.get_command_value(line)
                if segment_name == segment_to_rename:
                    code_list[i] = f"BeginSegment ({new_name})"
                    result["renamed"] += 1
            if line.lstrip().startswith("Parent"):
                parent_name = self.code.get_command_value(line)
                if parent_name == segment_to_rename:
                    code_list[i] = f'    Parent = "{new_name}"'
                    result["parent_changed"] += 1
        
        self.data_source["code"] = "\n".join(code_list) + "\n"

        return result
    
    def get_all_segments(self, names_only: bool = False) -> list:
        code_list = self.data_source["code"].split("\n")
        result = []
        segment_script = ""
        segment_name = ""
        for line in code_list:
            segment_script += line + "\n"
            if line.lstrip().startswith("BeginSegment"):
                segment_name = self.code.get_command_value(line)
                segment_script = line + "\n"
            if line.lstrip().startswith("EndSegment"):
                if segment_name:
                    if names_only:
                        result.append(segment_name)
                    else:
                        result.append(Segment(segment_script))
                    segment_name = ""

        return result

    def get_segments_map_name_parent(self, siblings_for: str = None) -> list:
        if siblings_for:
            segment = Segment(self._get_segment_script(siblings_for))
            search_for_parent = segment.parent

        code_list = self.data_source["code"].split("\n")
        result = []
        for line in code_list:
            if line.lstrip().startswith("BeginSegment"):
                segment_name = self.code.get_command_value(line)
            if line.lstrip().startswith("Parent"):
                parent = self.code.get_command_value(line)
                if segment_name:
                    if siblings_for:
                        if parent == search_for_parent:
                            result.append([segment_name, parent])
                    else:
                        result.append([segment_name, parent])
                    segment_name = ""
            if line.lstrip().startswith("EndSegment"):
                segment_name = ""

        return result

    def update_segment_code(self, segment_code_to_be_replaced: str, new_code_to_insert: str) -> str:
        replace_code_list = segment_code_to_be_replaced.split("\n")
        replace_with_list = new_code_to_insert.split("\n")

        old_code = ""
        for i in replace_code_list:
            if i.lstrip().startswith(("BeginSegment", "Parent", "Index")):
                old_code += i + "\n"

        new_code = ""
        for i in replace_with_list:
            if not i.lstrip().startswith(("BeginSegment", "Parent", "Index", "EndSegment")):
                new_code += i + "\n"
        
        result = old_code + new_code + "EndSegment"

        return result


        
        
        start_block = ""
        end_block = ""
        code_from_list = blocks_from_segment_code.split("\n")
        
        record_mode_start = False
        record_mode_end = False
        for line in code_from_list:
            if line.lstrip().startswith("DefineStartString"):
                record_mode_start = True
            if line.lstrip().startswith("DefineEndString"):
                record_mode_end = True
            if line.lstrip().startswith("EndDefineStartString"):
                start_block += line + "\n"
                record_mode_start = False
            if line.lstrip().startswith("EndDefineEndString"):
                end_block += line + "\n"
                record_mode_end = False

            if record_mode_start:
                start_block += line + "\n"
            if record_mode_end:
                end_block += line + "\n"
        
        code_to_replace_list = segment_code_to_be_replaced.split("\n")
        replaced_code = ""
        skipp_mode_start = False
        skipp_mode_end = False
        for line in code_to_replace_list:
            if line.lstrip().startswith("DefineStartString"):
                skipp_mode_start = True
            if line.lstrip().startswith("DefineEndString"):
                skipp_mode_end = True
            if line.lstrip().startswith("EndDefineStartString"):
                skipp_mode_start = False
                continue
            if line.lstrip().startswith("EndDefineEndString"):
                skipp_mode_end = False
                continue

            if line.lstrip().startswith("EndSegment"):
                replaced_code += start_block + "\n"
                replaced_code += end_block + "\n"
                replaced_code += line + "\n"
                continue

            if skipp_mode_end or skipp_mode_start:
                continue

            replaced_code += line + "\n"

        return replaced_code

    def _get_segment_script(self, segment_name: str) -> str:
        code_list = self.data_source["code"].split("\n")
        result = ""
        segment_code = False
        for line in code_list:
            if line.strip().startswith("BeginSegment"):
                if self.code.get_command_value(line) == segment_name:
                    segment_code = True
            
            if not segment_code:
                continue
            
            if line.strip().startswith("EndSegment"):
                segment_code = False
                result += line

            if segment_code:
                result += f"{line}\n"
        return result
            




