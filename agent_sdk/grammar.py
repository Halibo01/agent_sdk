import threading
import types
import typing

class GrammarBuilder:
    """
    Dynamically builds GBNF (Context-Free Grammar) for different formats.
    Fully customizable: Users can override default regexes or add new types dynamically.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.rules = {}
        self.rule_counter = 0
        self.format_type = "xml"

        # --- DYNAMIC TERMINAL RULES (REGEX) ---
        self.token_regex = {
            'int_val': '[0-9]+',
            'float_val': '[0-9]+ "." [0-9]+',
            'bool_val': '"true" | "false"',
            'email_val': '[a-zA-Z0-9_\\.-]+ "@" [a-zA-Z0-9_\\.-]+ "\\." [a-zA-Z]+',
            'date_val': '[0-9]{4} "-" [0-1][0-9] "-" [0-3][0-9]',
            'ws': '[ \\t\\n]*',
            'nl': '"\\n"'
        }

        self.custom_string_regex = None

        # --- SCHEMA TYPE ALIASES ---
        self.str = 'string_val'
        self.int = 'int_val'
        self.float = 'float_val'
        self.boolean = 'bool_val'
        self.email = 'email_val'
        self.date = 'date_val'

    def register_type(self, alias_name: str, token_name: str, regex: str):
        self.token_regex[token_name] = regex
        setattr(self, alias_name, token_name)

    def add_token(self, token_name: str, regex: str):
        self.token_regex[token_name] = regex

    def _reset(self, format_type):
        self.rules = {}
        self.rule_counter = 0
        self.format_type = format_type

    def _get_rule_name(self, base_name: str) -> str:
        self.rule_counter += 1
        return f"{base_name}_{self.rule_counter}"

    def _get_active_tokens(self) -> list:
        lines = []
        if self.custom_string_regex:
            lines.append(f'string_val ::= {self.custom_string_regex}')
        else:
            if self.format_type == "json":
                lines.append('string_val ::= "\\"" [^"]* "\\""')
            elif self.format_type == "xml":
                lines.append('string_val ::= [^<]+')
            else:
                lines.append('string_val ::= [^\\n]+')

        for token_name, regex in self.token_regex.items():
            lines.append(f'{token_name} ::= {regex}')

        return lines

    def to_xml(self, root_tag="root", **kwargs) -> str:
        with self._lock:
            self._reset("xml")
            root_content = self._process_dict(kwargs)
            lines = [f'root ::= "<{root_tag}>" {root_content} "</{root_tag}>"']
            for name, expr in self.rules.items():
                lines.append(f"{name} ::= {expr}")
            lines.extend(self._get_active_tokens())
            return "\n".join(lines)

    def to_json(self, **kwargs) -> str:
        with self._lock:
            self._reset("json")
            root_content = self._process_dict(kwargs)
            lines = [f'root ::= "{{" ws {root_content} ws "}}"']
            for name, expr in self.rules.items():
                lines.append(f"{name} ::= {expr}")
            lines.extend(self._get_active_tokens())
            return "\n".join(lines)

    def to_yaml(self, **kwargs) -> str:
        with self._lock:
            self._reset("yaml")
            root_content = self._process_dict(kwargs)
            lines = [f'root ::= {root_content}']
            for name, expr in self.rules.items():
                lines.append(f"{name} ::= {expr}")
            lines.extend(self._get_active_tokens())
            return "\n".join(lines)

    def to_markdown_table(self, **kwargs) -> str:
        if not kwargs:
            return ""
        with self._lock:
            self._reset("markdown")
            first_key = list(kwargs.keys())[0]
            list_type = kwargs[first_key]

            lines = []
            if typing.get_origin(list_type) is list:
                inner_dict = typing.get_args(list_type)[0]
                if isinstance(inner_dict, dict):
                    headers = list(inner_dict.keys())
                    header_row = "| " + " | ".join(headers) + " |\\n"
                    sep_row = "|" + "|".join(["---" for _ in headers]) + "|\\n"

                    row_rule = [self._process_node(inner_dict[h], h) for h in headers]
                    row_str = ' "\\"|\\"" '.join(row_rule)

                    lines.append(f'root ::= "{header_row}" "{sep_row}" row+')
                    lines.append(f'row ::= "\\"|\\"" {row_str} "\\"|\\\\n\\""')

            lines.extend(self._get_active_tokens())
            return "\n".join(lines)

    def _process_node(self, node_type, tag_name: str, is_last: bool = True) -> str:
        is_custom_alias = isinstance(node_type, str) and (node_type == 'string_val' or node_type in self.token_regex)

        if node_type is str: node_type = self.str
        elif node_type is int: node_type = self.int
        elif node_type is float: node_type = self.float
        elif node_type is bool: node_type = self.boolean

        if is_custom_alias or (isinstance(node_type, str) and (node_type == 'string_val' or node_type in self.token_regex)):
            if self.format_type == "xml":
                return f'"<{tag_name}>" {node_type} "</{tag_name}>"'
            elif self.format_type == "json":
                res = f'"\\"{tag_name}\\":" ws {node_type}'
                return res if is_last else f'{res} "," ws'
            else:
                return f'"\\"{tag_name}:\\" " " {node_type} nl'

        if node_type is type(None):
            if self.format_type == "xml":
                return f'"<{tag_name}></{tag_name}>"'
            else:
                res = f'"\\"{tag_name}\\":" ws "null"'
                return res if is_last else f'{res} "," ws'

        origin = typing.get_origin(node_type)
        if origin is typing.Union or type(node_type) is types.UnionType:
            args = typing.get_args(node_type)
            options = []
            for arg in args:
                if arg is type(None):
                    options.append('""' if self.format_type == "xml" else '"null"')
                elif arg is str or arg == self.str: options.append(self.str)
                elif arg is int or arg == self.int: options.append(self.int)
                elif arg is float or arg == self.float: options.append(self.float)
                elif arg is bool or arg == self.boolean: options.append(self.boolean)
                elif isinstance(arg, str) and (arg == 'string_val' or arg in self.token_regex):
                    options.append(arg)

            if self.format_type == "xml":
                return f'"<{tag_name}>" ( {" | ".join(options)} ) "</{tag_name}>"'
            else:
                res = f'"\\"{tag_name}\\":" ws ( {" | ".join(options)} )'
                return res if is_last else f'{res} "," ws'

        if origin is typing.Literal:
            args = typing.get_args(node_type)
            options = []
            for arg in args:
                if isinstance(arg, str):
                    options.append(f'"{arg}"' if self.format_type == "xml" else f'"\\"{arg}\\""')
                elif isinstance(arg, (int, float)):
                    options.append(f'"{arg}"')
                elif arg is None:
                    options.append('""' if self.format_type == "xml" else '"null"')

            rule_name = self._get_rule_name(f"{tag_name}_literal")
            self.rules[rule_name] = " | ".join(options)

            if self.format_type == "xml":
                return f'"<{tag_name}>" {rule_name} "</{tag_name}>"'
            else:
                res = f'"\\"{tag_name}\\":" ws {rule_name}'
                return res if is_last else f'{res} "," ws'

        if origin is list or origin is typing.List:
            inner_type = typing.get_args(node_type)[0]
            rule_name = self._get_rule_name(tag_name)

            if self.format_type == "xml":
                inner_content = self._process_type_raw(inner_type)
                self.rules[rule_name] = f'"<{tag_name}>" ( {inner_content} )* "</{tag_name}>"'
                return rule_name
            else:
                inner_content = self._process_type_raw(inner_type)
                array_rule = f'"[" ws ( {inner_content} ( ws "," ws {inner_content} )* )? ws "]"'
                self.rules[rule_name] = array_rule
                res = f'"\\"{tag_name}\\":" ws {rule_name}'
                return res if is_last else f'{res} "," ws'

        if isinstance(node_type, dict):
            content_rule = self._process_dict(node_type)
            rule_name = self._get_rule_name(tag_name)

            if self.format_type == "xml":
                self.rules[rule_name] = f'"<{tag_name}>" {content_rule} "</{tag_name}>"'
                return rule_name
            elif self.format_type == "yaml":
                self.rules[rule_name] = f'nl {content_rule}'
                res = f'"\\"{tag_name}:\\"" {rule_name}'
                return res
            else:
                self.rules[rule_name] = f'"{{" ws {content_rule} ws "}}"'
                res = f'"\\"{tag_name}\\":" ws {rule_name}'
                return res if is_last else f'{res} "," ws'

        if self.format_type == "xml":
            return f'"<{tag_name}>" {self.str} "</{tag_name}>"'
        elif self.format_type == "json":
            res = f'"\\"{tag_name}\\":" ws {self.str}'
            return res if is_last else f'{res} "," ws'
        elif self.format_type == "yaml":
            return f'"\\"{tag_name}:\\" " " {self.str} nl'
        else:
            return f'{self.str}'

    def _process_type_raw(self, node_type) -> str:
        if isinstance(node_type, dict):
            rule_name = self._get_rule_name("dict_item")
            content_rule = self._process_dict(node_type)
            if self.format_type == "xml":
                self.rules[rule_name] = content_rule
            else:
                self.rules[rule_name] = f'"{{" ws {content_rule} ws "}}"'
            return rule_name

        if node_type is str or node_type == self.str: return self.str
        if node_type is int or node_type == self.int: return self.int
        if isinstance(node_type, str) and node_type in self.token_regex: return node_type

        return self.str

    def _process_dict(self, d: dict) -> str:
        parts = []
        keys = list(d.keys())
        for i, key in enumerate(keys):
            val = d[key]
            is_last = (i == len(keys) - 1)
            parts.append(self._process_node(val, key, is_last))

        if self.format_type == "xml":
            return " ".join(parts)
        elif self.format_type == "yaml":
            return " nl ".join(parts)
        else:
            return " ws ".join(parts)
