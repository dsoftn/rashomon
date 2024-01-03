import os
import json
import urllib.request

from script_cls import Script
from segment_cls import Segment


class Rashomon():
    def __init__(self, project_filename: str = None) -> None:
        self._error_messages = []
        self.timeout_for_retriving_from_url = 3
        self._compatible_mode = False
        self.project_name = project_filename
        self._data_source = None
        self.script = Script()
        if project_filename:
            self.load_project(project_filename)

    def get_segment_selection(self, segment_name: str, remove_tags: bool = False, join_in_one_line: bool = False) -> str:
        if not self.project_name:
            self.errors(error_message="No project loaded.")
            return None
        text_dict = self.script.get_segment_text(segment_name=segment_name)
        if not text_dict:
            self.errors(error_message="Segment selection text could not be retrived.")
            return None
        if self._data_source["formated_text"]:
            txt = self._data_source["formated_text"]
        else:
            txt = self._data_source["text"]
        
        txt = txt[text_dict["start"]:text_dict["end"]]

        if remove_tags:
            txt = self.remove_tags(txt, join_in_one_line=join_in_one_line)

        return txt

    def get_segment_siblings(self, segment_name: str) -> list:
        if self._data_source is None:
            self.errors(error_message="No project loaded.")
            return None

        result = self.script.get_segments_map_name_parent(siblings_for=segment_name)
        return result

    def sort_segments(self, segments: list) -> list:
        if self._data_source is None:
            self.errors(error_message="No project loaded.")
            return None

        all_segments = self.script.get_all_segments(names_only=True)
        seg_data = []
        for segment in segments:
            if segment not in all_segments:
                return None
            segment_text = self.script.get_segment_text(segment)
            seg_data.append([segment, segment_text["start"]])
        
        seg_data.sort(key=lambda x: x[1])
        return [x[0] for x in seg_data]

    def recreate_segment_tree(self) -> bool:
        if self._data_source is None:
            self.errors(error_message="No project loaded.")
            return None

        code_tree = []
        for i in self.script.get_top_segment_names():
            descendants_list = []
            self._get_all_descendants(i, descendants_list)
            # descendants_list.pop(-1)
            code_tree.append([i, descendants_list])
        
        self._data_source["code"] = ""

        for top_level_segment in code_tree:
            self._data_source["code"] += top_level_segment[1][0][1]
            result = self._build_segment_tree(top_level_segment[0], top_level_segment[1], 0)
        return result

    def _build_segment_tree(self, segment_name: str, descendants_list: list, level: int):
        if level >= len(descendants_list):
            return True
        
        segment_code = descendants_list[level][1]
        segment = Segment(segment_code)

        siblings = []
        if segment.parent:
            siblings = self.script.get_segments_map_name_parent(siblings_for=segment_name)
        else:
            siblings.append([segment_name, None])
        
        has_children = None
        for seg in siblings:
            segment = Segment(self.script._get_segment_script(seg[0]))
            updated_code = self.script.update_segment_code(segment.code, segment_code)
            result = self.script.update_block_in_segment(seg[0], updated_code.strip(), replace_in_all_siblings=False)
            if result["errors"]:
                break
            if result["count"]:
                has_children = seg[0]
        
        if result["errors"]:
            return False
        
        seg_result = True
        if has_children:
            children = self.script.get_segment_children(has_children, names_only=True)
            seg_result = self._build_segment_tree(children[0], descendants_list, level + 1)
        
        return seg_result

    def _seg_name_from_code(self, code: str) -> str:
        for i in code.split("\n"):
            if i.lstrip().startswith("BeginSegment"):
                name = self.script.code.get_command_value(i)
                break
        return name

    def _get_all_descendants(self, segment_name, list_to_populate: list):
        segment_script = self.script._get_segment_script(segment_name=segment_name)
        
        list_to_populate.append([segment_name, segment_script])
        
        children = self.script.get_segment_children(segment_name=segment_name, names_only=True)
        if children:
            self._get_all_descendants(children[0], list_to_populate)
        return
        
    def _new_top_level_segment_code(self, segment_name: str = "Seg") -> str:
        result = f"""# Rashomon Code
BeginSegment ({segment_name})
    Parent = None
    Index = 0
EndSegment
"""
        return result

    def is_segment(self, segment_name: str) -> bool:
        if self._data_source is None:
            self.errors(error_message="No project loaded.")
            return None

        if segment_name in self.script.get_all_segments(names_only=True):
            return True
        else:
            return False

    def get_all_segments(self) -> list:
        if self._data_source is None:
            self.errors(error_message="No project loaded.")
            return None

        return self.script.get_all_segments(names_only=True)

    def get_segment_children(self, segment_name: str = None) -> list:
        if self._data_source is None:
            self.errors(error_message="No project loaded.")
            return None

        if segment_name is None:
            result = self.script.get_top_segment_names()
        else:
            result = self.script.get_segment_children(segment_name=segment_name, names_only=True)
        return result

    def remove_tags(self, text: str, join_in_one_line: bool = False, delimiter: str = "") -> str:
        result = ""
        in_tag = False
        pos = 0
        while pos < len(text):
            char = text[pos]
            if char == "<":
                in_tag = True
                pos += 1
                continue
            if char == ">":
                in_tag = False
                pos += 1
                continue
            if in_tag:
                pos += 1
                continue

            result += char
            pos += 1

        if join_in_one_line:
            result = delimiter.join(result.split("\n"))
        
        return result

    def remove_extra_spaces(self, text: str) -> str:
        if text is None:
            return None
        
        while True:
            text = text.replace("  ", " ")
            if text.find("  ") == -1:
                break
        return text.strip()

    def loaded_project(self) -> str:
        return self.project_name

    def load_project(self, project_filename: str = None, change_source: str = None) -> bool:
        if not os.path.isfile(project_filename):
            self.errors(error_message="The file does not exist.")
            self._data_source = None
            self.project_name = None
            return False
        
        try:
            with open(project_filename, "r", encoding="utf-8") as file:
                self._data_source = json.load(file)
        except Exception as e:
            self.errors(e)
            self._data_source = None
            self.project_name = None
            return False
        
        if change_source:
            self._data_source["source"] = change_source

        if not self._data_source["text"]:
            result = self.download_text_from_source()
            if not result:
                self.errors(error_message="The text could not be retrieved from the source.")
                self._data_source = None
                self.project_name = None
                return False

        self.project_name = project_filename
        self.script.load_data_source(self._data_source)
    
    def get_source(self) -> str:
        if self._data_source is None:
            self.errors(error_message="No project loaded.")
            return None

        return self._data_source["source"]
    
    def get_source_text(self) -> str:
        if self._data_source is None:
            self.errors(error_message="No project loaded.")
            return None

        if self._compatible_mode:
            if self._data_source["formated_text"]:
                return self._data_source["formated_text"]
            else:
                return self._data_source["text"]
        else:
            return self._data_source["text"]
        
    def set_compatible_mode(self, value: bool):
        if not isinstance(value, bool):
            self.errors(error_message="Set Compatible Mode: Value must be boolean True/False")
            return None
        
        if self._data_source is None:
            self.errors(error_message="No project loaded.")
            return None
        
        self._compatible_mode = value
        if not value:
            self._data_source["formated_text"] = ""
            return
        
        from bs4 import BeautifulSoup as bs

        soup = bs(self._data_source["text"], 'html.parser')
        formatted_text = soup.prettify()
        self._data_source["formated_text"] = formatted_text
    
    def is_compatible_mode(self) -> bool:
        return self._compatible_mode

    def errors(self, error_message: str = None, clear_errors: bool = False) -> list:
        if clear_errors:
            self._error_messages = []
        
        if error_message:
            self._error_messages.append(error_message)
        
        return self._error_messages

    def download_text_from_source(self) -> bool:
        if self._data_source is None:
            self.errors(error_message="No project loaded.")
            return None
        txt = ""
        if self._data_source["selected"] == "file":
            txt = self._retrive_text_from_file(self._data_source["source"])
            if txt is None:
                return False
        elif self._data_source["selected"] == "web":
            txt = self._retrive_text_from_url(self._data_source["source"])
            if txt is None:
                return False
        self._data_source["text"] = txt
        return True
        
    def _retrive_text_from_file(self, filename: str) -> str:
        if not os.path.isfile(filename):
            return None
        
        result = ""
        try:
            with open(filename, "r", encoding="utf-8") as file:
                result = file.read()
        except Exception as e:
            self.errors(error_message=e)
            return None
        
        return result
    
    def _retrive_text_from_url(self, url: str) -> str:
        result = ""
        try:
            result = urllib.request.urlopen(url, timeout=self.timeout_for_retriving_from_url).read().decode("utf-8")
        except Exception as e:
            self.errors(error_message=e)
            return None
        
        return result
