import json


class InteractionLogger:
    def __init__(self, log_filepath):
        self.file = open(log_filepath, "a")

    def close(self):
        if self.file:
            self.file.close()

    def write(self, data):
        self.file.write(json.dumps(data) + "\n")
        self.file.flush()
