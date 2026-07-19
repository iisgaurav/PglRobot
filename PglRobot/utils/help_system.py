# Registry mapping plugin names to their help strings
HELP_DICT: dict[str, str] = {}

def register_help(module_name: str, help_text: str):
    """
    Register a module and its help string for the /help menu.
    """
    HELP_DICT[module_name] = help_text

def get_help(module_name: str) -> str:
    """
    Retrieve the help string for a specific module.
    """
    return HELP_DICT.get(module_name, "No help available for this module.")

def get_all_modules() -> list[str]:
    """
    Return a list of all registered module names, sorted alphabetically.
    """
    return sorted(list(HELP_DICT.keys()))
