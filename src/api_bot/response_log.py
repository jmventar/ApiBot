import datetime


class ResponseLog:
    def __init__(
        self,
        method: str,
        url: str,
        status_code: int,
        content_type,
        content_length: int,
        data=None,
        truncated: bool = False,
    ):
        self.method = method
        self.url = url
        self.status_code = status_code
        self.content_type = content_type
        self.content_length = content_length
        self.data = data
        self.truncated = truncated
        self.datetime = datetime.datetime.now()

    def to_json(self):
        data = {
            "datetime": self.datetime,
            "method": self.method,
            "url": self.url,
            "status": self.status_code,
            "content-type": self.content_type,
            "content-length": self.content_length,
            "content-truncated": self.truncated,
        }

        if self.data is not None:
            data["data"] = self.data

        return data
