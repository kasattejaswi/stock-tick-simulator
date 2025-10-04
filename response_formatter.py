import copy


class ResponseFormatter:
    def __init__(self, template=None):
        """Initialize response formatter with optional custom template."""
        self.template = template
        self.default_template = {
            "symbol": "{{SYMBOL}}",
            "timestamp": "{{TIMESTAMP}}",
            "price": "{{TICK}}"
        }
    
    def format_response(self, symbol, timestamp, tick_price):
        """Format a response using the template and provided values."""
        template_to_use = self.template if self.template else self.default_template
        response = copy.deepcopy(template_to_use)
        return self._replace_placeholders(response, symbol, timestamp, tick_price)
    
    def _replace_placeholders(self, obj, symbol, timestamp, tick_price):
        """Recursively replace placeholders in the template."""
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                new_key = self._replace_string(key, symbol, timestamp, tick_price)
                result[new_key] = self._replace_placeholders(value, symbol, timestamp, tick_price)
            return result
        elif isinstance(obj, list):
            return [self._replace_placeholders(item, symbol, timestamp, tick_price) for item in obj]
        elif isinstance(obj, str):
            return self._replace_string(obj, symbol, timestamp, tick_price)
        else:
            return obj
    
    def _replace_string(self, text, symbol, timestamp, tick_price):
        """Replace placeholder strings with actual values."""
        if not isinstance(text, str):
            return text
        
        result = text.replace("{{SYMBOL}}", symbol)
        result = result.replace("{{TIMESTAMP}}", str(timestamp))
        result = result.replace("{{TICK}}", str(tick_price))
        
        if result == str(timestamp):
            return timestamp
        if result == str(tick_price):
            return tick_price
        
        return result
