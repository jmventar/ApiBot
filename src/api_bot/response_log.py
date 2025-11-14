import datetime


class ResponseLog:
    def __init__(self, response, content_length: int, is_json_response: bool):
        self.response = response
        self.content_length = content_length
        self.is_json_response = is_json_response
        self.datetime = datetime.datetime.now()

    def to_json(self):
        data = {
            "datetime": self.datetime,
            "method": self.response.request.method,
            "url": self.response.url,
            "status": self.response.status_code,
            "content-type": self.response.headers.get("content-type"),
            "content-length": self.content_length,
        }

        if self.content_length > 0:
            if self.is_json_response:
                data["data"] = self.response.json()
            else:
                data["data"] = self.response.text()

        return data
