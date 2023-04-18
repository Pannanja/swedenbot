from scripts.config import config

software_model = config.get('model','software_model')

def user_input(prompt: str, input_type: type):
    """
    Asks for user input.

    Args:
        prompt: The prompt the user will see
        input_type: The type of data needed
    """
    if input_type == bool:
        result = user_input_bool(prompt)
        return result
    elif input_type == str:
        result = user_input_string(prompt)
        return result

def user_input_bool(prompt):
    response = input(f"{prompt} Y/N: ")
    if response.lower() == "y" or software_model == "txt_file_input":
        return True
    else:
        return False

def user_input_string(prompt):
    if software_model != "txt_file_input":
        return input(f"{prompt}: ")
    else:
        return False
