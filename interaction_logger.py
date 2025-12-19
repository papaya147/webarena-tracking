import json
import pathlib


class InteractionLogger:
    def __init__(self, log_filepath):
        parent_dir = pathlib.Path(log_filepath).parent
        parent_dir.mkdir(parents=True, exist_ok=True)
        self.file = open(log_filepath, "w")

    def close(self):
        if self.file:
            self.file.close()

    def write(self, data):
        self.file.write(json.dumps(data) + "\n")
        self.file.flush()
