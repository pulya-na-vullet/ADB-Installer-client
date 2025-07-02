class Device:
    def __init__(self, device_id, status):
        self.device_id = device_id
        self.status = status

class Package:
    def __init__(self, name, version, device_id):
        self.name = name
        self.version = version
        self.device_id = device_id