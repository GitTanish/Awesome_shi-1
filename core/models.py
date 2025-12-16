from enum import Enum

class RouteIntent(Enum):
    CODE ="CODE"
    RESEARCH = "RESEARCH"
    CASUAL = "CASUAL"

    @classmethod
    def list_options(cls):
        return ", ".join([e.value for e in cls])