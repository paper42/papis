from typing import Optional, List, Callable, Any
import re


def confirm(prompt_string: str,
            yes: bool = True,
            bottom_toolbar: Optional[str] = None) -> bool:
    """Confirm with user input

    :param prompt_string: Question or text that the user gets.
    :type  prompt_string: str
    :param yes: If yes should be the default.
    :type  yes: bool
    :returns: True if go ahead, False if stop
    :rtype:  bool

    """
    result = prompt(prompt_string,
                    bottom_toolbar=bottom_toolbar,
                    default='Y/n' if yes else 'y/N',
                    validator_function=lambda x: x in 'YyNn',
                    dirty_message='Please, write either "y" or "n" to confirm')
    if yes:
        return result not in 'Nn'
    return result in 'Yy'


def text_area(title: str,
              text: str,
              lexer_name: str = "",
              height: int = 10,
              full_screen: bool = False) -> str:
    """
    Small implementation of an editor/pager for small pieces of text.

    :param title: Title of the text_area
    :type  title: str
    :param text: Editable text
    :type  text: str
    :param lexer_name: If the editable text should be highlighted with
        some kind of grammar, examples are ``yaml``, ``python`` ...
    :type  lexer_name: str
    :param height: Max height of the text area
    :type  height: int
    :param full_screen: Wether or not the text area should be full screen.
    :type  full_screen: bool
    """
    from prompt_toolkit import Application
    from prompt_toolkit.enums import EditingMode
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout.containers import HSplit, Window, WindowAlign
    from prompt_toolkit.layout.controls import (BufferControl,
                                                FormattedTextControl)
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.layout import Dimension
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.key_binding.key_processor import KeyPressEvent
    from prompt_toolkit.lexers import PygmentsLexer
    from pygments.lexers import find_lexer_class_by_name

    kb = KeyBindings()
    text_buffer = Buffer()
    text_buffer.text = text
    should_save = False

    @kb.add('c-q')  # type: ignore
    def exit_(event: KeyPressEvent) -> None:
        event.app.exit()

    @kb.add('c-s')  # type: ignore
    def save_(event: KeyPressEvent) -> None:
        should_save = True

    text_height = Dimension(min=0, max=height) if height is not None else None

    pygment_lexer = find_lexer_class_by_name(lexer_name)
    lexer = PygmentsLexer(pygment_lexer)
    text_window = Window(height=text_height,
                         style='bg:black fg:ansiwhite',
                         content=BufferControl(
                             buffer=text_buffer, lexer=lexer))

    root_container = HSplit([
        Window(
            align=WindowAlign.LEFT,
            style='bg:ansiwhite',
            height=1,
            content=FormattedTextControl(
                text=[('fg:ansiblack bg:ansiwhite', title)]
            ),
            always_hide_cursor=True
        ),

        text_window,

        Window(
            height=1,
            width=None,
            align=WindowAlign.LEFT,
            style='bg:ansiwhite',
            content=FormattedTextControl(
                text=[(
                    'fg:ansiblack bg:ansiwhite',
                    "Quit [Ctrl-q]  Save [Ctrl-s]"
                )]
            )
        ),
    ])

    layout = Layout(root_container)

    layout.focus(text_window)

    app = Application(editing_mode=EditingMode.EMACS,
                      layout=layout,
                      erase_when_done=True,
                      key_bindings=kb,
                      full_screen=full_screen)  # type: Application[Any]
    app.run()
    return text_buffer.text if should_save else ""


def yes_no_dialog(title: str, text: str) -> Any:
    from prompt_toolkit.shortcuts import yes_no_dialog as yesno
    from prompt_toolkit.styles import Style

    example_style = Style.from_dict({
        'dialog': 'bg:#88ff88',
        'dialog frame-label': 'bg:#ffffff #000000',
        'dialog.body': 'bg:#000000 #00ff00',
        'dialog shadow': 'bg:#00aa00',
    })

    return yesno(title=title, text=text, style=example_style)


def prompt(prompt_string: str,
           default: str = "",
           bottom_toolbar: Optional[str] = None,
           multiline: bool = False,
           validator_function: Optional[Callable[[str], bool]] = None,
           dirty_message: str = "") -> str:
    """Prompt user for input

    :param prompt_string: Question or text that the user gets.
    :type  prompt_string: str
    :param default: Default value to give if the user does not input anything
    :type  default: str
    :returns: User input or default
    :rtype:  bool

    """
    import prompt_toolkit
    from prompt_toolkit.validation import Validator
    from prompt_toolkit.formatted_text.base import to_formatted_text
    validator = None  # type: Optional[Validator]
    if validator_function is not None:
        validator = Validator.from_callable(validator_function,
                                            error_message=dirty_message,
                                            move_cursor_to_end=True)

    fragments = to_formatted_text([('', prompt_string),
                                   ('fg:red', ' ({0})'.format(default)),
                                   ('', ': ')])

    result = prompt_toolkit.prompt(fragments,
                                   validator=validator,
                                   multiline=multiline,
                                   bottom_toolbar=bottom_toolbar,
                                   validate_while_typing=True)

    return str(result) if result else default


def get_range(range_str: str) -> List[int]:
    range_regex = re.compile(r"(\d+)-?(\d+)?")
    try:
        return sum([
            list(range(int(p[0]), int(p[1] if p[1] else p[0])+1))
            for p in range_regex.findall(range_str)], [])
    except ValueError:
        return []


def select_range(options: List[Any], message: str) -> List[int]:
    for i, o in enumerate(options):
        print("{i}. {o}".format(i=i, o=o))

    possible_indices = range(len(options))
    all_keywords = ["all", "a"]

    if not options:
        return []

    selection = prompt(
        prompt_string=message,
        default="",
        dirty_message="Range not valid, example: 0, 2, 3-10, a, all, ...",
        validator_function=lambda string:
                string in all_keywords or
                len(set(get_range(string)) & set(possible_indices)) > 0)

    if selection in all_keywords:
        selection = ",".join(map(str, range(len(options))))

    return [i for i in get_range(selection) if i in possible_indices]
