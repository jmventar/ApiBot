import datetime


class ResponseLog:
    def __init__(self, response):
        self.response = response
        self.datetime = datetime.datetime.now()

    def to_json(self):
        data = {
            "datetime": self.datetime,
            "method": self.response.request.method,
            "url": self.response.url,
            "status": self.response.status_code,
            "content-type": self.response.headers.get("content-type"),
            "content-length": self.response.headers.get("content-length"),
            "data": self.response.json(),
        }
        return data
