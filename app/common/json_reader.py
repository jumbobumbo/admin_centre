import json


class JSONReads:
    """
    Example: JSONReads(json_file).json_data["connection"]["ip_add"]
    """

    def __init__(self, json_file: json):
        """
        json_file: Path OBJ to (and including) json file
        """
        self.json_data = json_file

    @property
    def json_data(self) -> dict:
        return self.__json_data

    @json_data.setter
    def json_data(self, json_file):
        with open(json_file, "r") as f:
            self.__json_data = json.load(f)

    def data_return(self) -> dict:
        """
        returns the data (which is now a dict)
        """
        return self.json_data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self.json_data}"
