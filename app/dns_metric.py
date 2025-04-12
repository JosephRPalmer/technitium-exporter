class dns_metric:

    def __init__(self, name, current_value, total_today, last_updated=None):
        self.name = name
        self.current_value = current_value
        self.total_today = total_today
        self.last_updated = last_updated
