from scripts.config import config

def user_input(prompt: str, input_type: type):
    #software_model = config.get('model','software_model')
    if input_type == bool:
        #if software_model == "console":
            response = input(f"{prompt} Y/N: ")
            if response.lower() == "y":
                return True
            else:
                return False
    elif input_type == str:
        #if software_model == "console":
            return input(f"{prompt}: ")
