import json

class Tool:
    def __init__(self, data):
        self.title = data['title']
        self.description = data['description']
        self.code = data['code']

        exec(self.code)
        self.fn = locals()[self.title]

    def __call__(self, *args, **kwargs):
        return self.fn(*args,**kwargs)