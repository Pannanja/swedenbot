import sys
from scripts import init
from scripts import chat_gpt
from scripts.config import config
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time
import threading

class txt_file_watcher(FileSystemEventHandler):
    def process_file(self, event):
        file_extension = os.path.splitext(event.src_path)[1]
        if file_extension.lower() == ".txt":
            file_name = os.path.basename(event.src_path)
            print (f"File found: {file_name}\nProcessing...")
            with open(event.src_path, 'r', encoding='utf-8') as file:
                user_question = file.read()
            response, references = chat_gpt.ask_swedenbot(user_question, save_data_cache, temperature)
            references = "\n\n".join(references)
            output = f"{response}\n\nSources:\n\n{references}"
            output_path = os.path.join(txt_output,file_name)
            with open(output_path, "w", encoding='utf-8') as file:
                file.write(output)
            print(f"Response created: {file_name}")
            os.remove(event.src_path)
            print("Question removed")
        return
    
    def on_created(self, event):
        try:
            if event.is_directory:
                return
            processing_thread = threading.Thread(target=self.process_file, args=(event,))
            processing_thread.start()
        except Exception as e:
            print(f"Error: {e}")
        


software_model = config.get('model','software_model')
temperature = float(config.get('openai_properties','temperature'))
txt_input = config.get('data','txt_input')
txt_output = config.get('data','txt_output')

save_data_cache = init.init_swedenbot()

if software_model == "ncbs":
    user_question = sys.argv[1]
    chat_gpt.ask_swedenbot(user_question, save_data_cache, temperature)
elif software_model == "console":
    while True:
        user_question = input("Ask Question: ")
        chat_gpt.ask_swedenbot(user_question, save_data_cache, temperature)
elif software_model == "txt_file_input":
    event_handler = txt_file_watcher()
    observer = Observer()
    observer.schedule(event_handler,txt_input, recursive=False)
    observer.start()
    print("Waiting for input...")
    while True:
        time.sleep(1)

