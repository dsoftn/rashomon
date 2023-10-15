import copy
import time
import random
import html


class TextToHtmlRule():
    """
    TextToHtmlRule class to define styling rules for converting text to HTML.

    Parameters:

        text (str): The text to match this rule to.

        replace_with (str): Optional text to replace matched text with.

        bg_color (str): Background color.

        fg_color (str): Foreground/text color.

        font_family (str): Font family.

        font_size (int): Font size in px.

        font_bold (bool): Whether to bold text.

        font_italic (bool): Whether to italicize text. 

        font_underline (bool): Whether to underline text.

        letter_spacing (int): Letter spacing in px.

        line_height (float): Line height.

        text_align (str): Text alignment - left, right, center, justify.

        vertical_align (str): Vertical alignment - top, middle, bottom.

        white_space_wrap (bool): Whether to wrap text.

        text_opacity (float): Text opacity from 0 to 1.
        
    Methods:

        set_text_shadow(): Sets text shadow property.

        set_default_simple_shadow(): Applies default subtle shadow.

        set_default_offset_shadow(): Applies default offset shadow.

        set_default_blurred_shadow(): Applies default blurred shadow.

        get_text(): Gets rule match text, with new line as <br>.

        set_text(): Sets rule match text.

        get_css_style_content(): Gets full CSS style string for rule.

        has_css_style(): Checks if rule has any styling set.

    """

    def __init__(
            self,
            text: str = "",
            replace_with: str = None,
            bg_color: str = None,
            fg_color: str = None,
            font_family: str = None,
            font_size: int = None,
            font_bold: bool = None,
            font_italic: bool = None,
            font_underline: bool = None,
            letter_spacing: int = None,
            line_height: float = None,
            text_align: str = None,
            vertical_align: str = None,
            white_space_wrap: bool = None,
            text_opacity: float = None
            ) -> None:
        
        self.text = text
        self.replace_with = replace_with
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.font_family = font_family
        self.font_size = font_size
        self.font_bold = font_bold
        self.font_italic = font_italic
        self.font_underline = font_underline
        self.letter_spacing = letter_spacing
        self.line_height = line_height
        self.text_align = text_align
        self.vertical_align = vertical_align
        self.white_space_wrap = white_space_wrap
        self.text_opacity = text_opacity
        
        self.text_shadow = None

        self.rule_name = f"{time.time_ns()} + {random.randint(0, 1000000)}"

    def set_text_shadow(
            self,
            offset_x: int = 0,
            offset_y: int = 0,
            blur_radius: int = 0,
            color: str = "black"
            ):
        """
        Sets the text shadow CSS property.

        Parameters:

            offset_x (int): Horizontal shadow offset in pixels. Default 0.  

            offset_y (int): Vertical shadow offset in pixels. Default 0.

            blur_radius (int): Blur radius for the shadow. Default 0.

            color (str): Color of the shadow as a CSS value. Default 'black'.

        Sets the text_shadow property to a string value with the provided parameters.

        This will set a text shadow effect on the text when applied in CSS.

        For example:

        set_text_shadow(offset_x=2, offset_y=2, color='grey')

        Would set a 2px horizontal and vertical grey shadow.

        """
        
        shadow = f'{offset_x}px {offset_y}px {blur_radius}px {color}'
        self.text_shadow = shadow

    def set_default_simple_shadow(self):
        self.set_text_shadow(offset_x=2,
                             offset_y=2,
                             color="black"
                             )
        
    def set_default_offset_shadow(self):
        self.set_text_shadow(offset_x=5,
                             offset_y=5,
                             blur_radius=2,
                             color="red"
                             )

    def set_default_blurred_shadow(self):
        self.set_text_shadow(offset_x=0,
                             offset_y=0,
                             blur_radius=5,
                             color="rgba(0,0,0,0.5)"
                             )

    def get_text(self) -> str:
        """
        Gets the text that will be matched for this rule.

        If replace_with is set, returns that text with newlines converted to <br>.
        Otherwise returns the original text value with newlines converted.

        The _fix_string() method handles converting newlines to <br> tags.

        Returns:
            str: The text to match for this rule, with newlines as <br>.
        """

        if self.replace_with:
            return self._fix_string(self.replace_with)
        else:
            return self._fix_string(self.text)

    def set_text(self, text: str):
        self.text = text
        
    def _fix_string(self, text: str) -> str:
        if text:
            text = text.replace("\n", "<br>")
        return text

    def get_css_style_content(self, general_rule = None) -> str:
        """
        Generates a CSS style string for the rule based on set properties.

        Iterates through all style properties set on the rule and generates 
        a CSS style string concatenating property:value pairs.

        Removes any trailing whitespace and returns the style string.

        Returns an empty string if no properties are set.

        Returns:
            str: CSS style string for the rule.
        """

        style = ""

        if self.bg_color is not None:
            style += f" background-color: {self.bg_color}; "
        else:
            if general_rule:
                if general_rule.bg_color:
                    style += f" background-color: {general_rule.bg_color}; "

        if self.fg_color is not None:
            style += f" color: {self.fg_color}; "
        else:
            if general_rule:
                if general_rule.fg_color:
                    style += f" color: {general_rule.fg_color}; "

        if self.font_family is not None:
            style += f" font-family: {self.font_family}; "
        else:
            if general_rule:
                if general_rule.font_family:
                    style += f" font-family: {general_rule.font_family}; "

        if self.font_size is not None:
            style += f" font-size: {self.font_size}px; "
        else:
            if general_rule:
                if general_rule.font_size:
                    style += f" font-size: {general_rule.font_size}px; "

        if self.font_bold is not None:
            if self.font_bold:
                style += " font-weight: bold; "
        else:
            if general_rule:
                if general_rule.font_size:
                    style += f" font-size: {general_rule.font_size}px; "

        if self.font_italic is not None:
            if self.font_italic:
                style += " font-style: italic; "
        else:
            if general_rule:
                if general_rule.font_italic:
                    style += " font-style: italic; "

        if self.font_underline is not None:
            if self.font_underline:
                style += " font-decoration: underline; "
        else:
            if general_rule:
                if general_rule.font_underline:
                    style += " font-decoration: underline; "

        if self.letter_spacing is not None:
            style += f" letter-spacing: {self.letter_spacing}px; "
        else:
            if general_rule:
                if general_rule.letter_spacing:
                    style += f" letter-spacing: {general_rule.letter_spacing}px; "

        if self.line_height is not None:
            style += f" line-height: {self.line_height}; "
        else:
            if general_rule:
                if general_rule.line_height:
                    style += f" line-height: {general_rule.line_height}; "

        if self.text_align is not None:
            style += f" text-align: {self.text_align}; "
        else:
            if general_rule:
                if general_rule.text_align:
                    style += f" text-align: {general_rule.text_align}; "

        if self.vertical_align is not None:
            style += f" vertical-align: {self.vertical_align}; "
        else:
            if general_rule:
                if general_rule.vertical_align:
                    style += f" vertical-align: {general_rule.vertical_align}; "

        if self.white_space_wrap is not None:
            if self.white_space_wrap:
                style += " white-space: wrap; "
            else:
                style += " white-space: nowrap; "
        else:
            if general_rule:
                if general_rule.white_space_wrap:
                    if general_rule.white_space_wrap:
                        style += " white-space: wrap; "
                    else:
                        style += " white-space: nowrap; "

        if self.text_opacity is not None:
            style += f" opacity: {self.text_opacity}; "
        else:
            if general_rule:
                if general_rule.text_opacity:
                    style += f" opacity: {general_rule.text_opacity}; "

        if self.text_shadow is not None:
            style += f" text-shadow: {self.text_shadow}; "
        else:
            if general_rule:
                if general_rule.text_shadow:
                    style += f" text-shadow: {general_rule.text_shadow}; "

        if style:
            style = style.rstrip(" ")
        
        return style

    def has_css_style(self) -> bool:
        if self.get_css_style_content():
            return True
        else:
            return False


class TextToHTML():
    """
    TextToHTML class to convert text to HTML with styling rules.

    Parameters:
        text (str): The text to convert to HTML.

    Attributes:
        text (str): The original text.
        rules (list): List of TextToHtmlRule objects. 
        general_rule (TextToHtmlRule): Default rule applied.

    Methods:

        reset_general_rule(): Reset general rule to default.

        set_text(): Set the text to convert.

        get_text(): Get the original text.

        add_rule(): Add a TextToHtmlRule to rules.

        delete_rule(): Delete a rule, or clear all rules.

        get_html(): Generate and return HTML string.

    Converts text to HTML by applying a general rule and additional
    specific rules. Rules match text snippets and define styling.
    """

    def __init__(self, text: str = "") -> None:

        self.text = self._fix_string(text)

        self.rules: list = []
        self.general_rule = TextToHtmlRule()

    def reset_general_rule(self):
        """
        Resets the general_rule attribute to a new TextToHtmlRule instance.

        This will reset any custom styling set on the existing general rule.
        The general rule is applied to any text not matched by other specific rules.
        """

        self.general_rule = TextToHtmlRule()

    def set_text(self, text: str):
        """
        Sets the text attribute to the provided text string.

        Parameters:
            text (str): The text to convert to HTML.

        Calls _fix_string() on the text to convert newlines to <br> tags.
        Sets the text attribute to the converted string.
        """

        self.text = self._fix_string(text)
    
    def get_text(self) -> str:
        """
        Gets the original text that was passed to the TextToHTML class.

        Returns:
            str: The original text string.
        """

        return self.text

    def add_rule(self, rule: TextToHtmlRule) -> None:
        """
        Adds a TextToHtmlRule object to the rules list.

        Parameters:
            rule (TextToHtmlRule): The rule object to add.

        Appends the rule to the end of the rules list.
        """
        if isinstance(rule, TextToHtmlRule):
            self.rules.append(rule)
        else:
            for i in rule:
                self.rules.append(i)

    def delete_rule(self, rule: TextToHtmlRule = None) -> bool:
        """
        Deletes a rule from the rules list.

        Parameters:
            rule (TextToHtmlRule): The rule object to delete.

        If rule is None, clears all rules in the list.

        Otherwise, loops through the rules list and removes 
        the rule with matching rule_name.

        Returns:
            bool: True if rule was deleted, False otherwise.
        """

        if isinstance(rule, TextToHtmlRule):
            return self._delete_rule(rule)
        else:
            success = True
            for item in rule:
                if not self._delete_rule(item):
                    success = False
        return success

    def _delete_rule(self, rule: TextToHtmlRule = None) -> bool:
        if rule is None:
            self.rules = []
            return True
        
        for idx, item in enumerate(self.rules):
            if item.rule_name == rule.rule_name:
                self.rules.pop(idx)
                return True
        return False

    def get_html(self) -> str:
        """
        Generates and returns the HTML string by applying rules.

        Checks that text is not empty, then gets a list of text slices 
        and matched rules using _get_slices(). 

        If there are slices, calls _create_html() to generate the HTML by 
        applying the rules on each text slice.

        Returns:
            str: The generated HTML string.
        """

        if not self.text:
            return ""

        slices = self._get_slices(self.text)
        html = None
        if slices:
            html = self._create_html(self.text, slices)
        
        return html

    def _fix_string(self, text: str) -> str:
        if text:
            text = text.replace("\n", "<br>")
        return text

    def _create_html(self, text: str, slices: list) -> str:
        result = ""
        for i in slices:
            style = i[2].get_css_style_content(self.general_rule)
            if style:
                style = f' style="{style}"'

            text_for_html = i[2].get_text().replace("\n", "<br>")
            txt = f'<span{style}>{text_for_html}</span>'
            result += txt
        
        return result

    def _get_slices(self, text: str) -> list:
        if not text:
            return []

        rule_positions = []

        for rule in self.rules:
            if rule.text:
                pos = self._get_rule_pos(text, rule)
                for i in pos:
                    rule_positions.append([i[0], i[1], rule])
        
        rule_positions.sort(key=lambda x: x[0])

        result = []
        pos = 0
        for item in rule_positions:
            if item[0] < pos:
                continue
            rule = self._get_general_rule(text, pos, item[0])
            if rule:
                result.append([pos, item[0], rule])
            result.append([item[0], item[1], item[2]])
            pos = item[1]

        if result:
            pos = result[-1][1]
        rule = self._get_general_rule(text, pos, None)
        if rule:
            result.append([pos, len(text), rule])

        return result

    def _get_general_rule(self, text: str, start_pos: int = None, end_pos: int = None) -> TextToHtmlRule:
        if start_pos is None:
            start_pos = 0
        if end_pos is None:
            end_pos = len(text)
        if end_pos - start_pos == 0:
            return None
        
        rule = copy.deepcopy(self.general_rule)
        rule.set_text(text[start_pos:end_pos])

        return rule

    def _get_rule_pos(self, text: str, rule: TextToHtmlRule) -> list:
        positions = []
        pos = 0
        while True:
            pos = text.find(rule.text, pos)
            if pos >= 0:
                start = pos
                end = start + len(rule.text)
                positions.append((start, end))
                pos += 1
            else:
                break
        
        return positions


class TextToHtmlConverter:
    def __init__(self, text: str = None) -> None:
        self.text = text

    def convertet_text(self, text: str = None) -> str:
        if text is None:
            text = self.text
        if text is None:
            return None
        
        styles = """
        <style>
        .c_html { color: #ff0000; }
        .c_head { color: #00ff00; }
        .c_title { color: #0000ff; }
        .c_meta { color: #ff9900; }
        .c_link { color: #0099cc; }
        .c_style { color: #8800cc; }
        .c_script { color: #cc0099; }
        .c_body { color: #333333; }
        .c_h1 { color: #990000; }
        .c_h2 { color: #006600; }
        .c_p { color: #000099; }
        .c_a { color: #ff00ff; }
        .c_img { color: #cc66ff; }
        .c_ul { color: #009999; }
        .c_ol { color: #996600; }
        .c_li { color: #ffcc00; }
        .c_div { color: #aaffff; }
        .c_span { color: #ff6600; }
        .c_table { color: #3399cc; }
        .c_tr { color: #ff33cc; }
        .c_td { color: #cc9933; }
        .c_form { color: #990099; }
        .c_input { color: #00cc00; }
        .c_button { color: #ff6600; }
        .c_textarea { color: #006666; }
        .c_select { color: #ffcc33; }
        .c_iframe { color: #660066; }
        .c_text { font-weight: bold; color: #ffffff; }
        .c_undefined { color: #c078ff; }
        </style>
        """
        styles_list = [
    "html", "head", "title", "meta", "link", "style", "script", "body",
    "h1", "h2", "p", "a", "img", "ul", "ol", "li", "div", "span",
    "table", "tr", "td", "form", "input", "button", "textarea", "select", "iframe"
]

        txt = html.escape(text)
        txt = txt.replace("\n", "<br>")
        body = ""
        pos = 0
        start = 0
        end = 0

        while True:
            if pos >= len(txt):
                break
            pos = txt.find("&lt;", pos)
            if pos == -1:
                body += f'{txt[end+4:]}'
                break
            
            if end > 0:
                if end + 4 < pos:
                    body += f'<span class="c_text">{txt[end+4:pos]}</span>'

            start = pos
            end = txt.find("&gt;", pos)
            if end == -1:
                body += txt[start:]
                break

            tag = txt[start+4:end] + " "
            tag = tag[:tag.find(" ")]
            class_name = ""
            if tag in styles_list:
                class_name = f"c_{tag}"
            else:
                class_name = "c_undefined"
            
            body += f'<span class="{class_name}">{txt[start:end+4]}</span>'
            pos = end + 4

        html_text = f"""<html>
<head>
{styles}
</head>
<body>
{body}
</body>
</html>

"""
        return html_text