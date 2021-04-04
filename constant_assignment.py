class Limit:
    def __init__(self, min_val=None, max_val=None):
        self.min_val = min_val
        self.max_val = max_val
    def clone(self):
        return Limit(self.min_val, self.max_val)

class VariableMap:
    def __init__(self, default_min=0, default_max=999):
        self.default_min = default_min
        self.default_max = default_max
        self.limits = {}
    def remove_var(self, var):
        if var in self.limits:
            self.limits.pop(var)
    def has_min(self, var):
        return var in self.limits and not self.limits[var].min_val is None
    def has_max(self, var):
        return var in self.limits and not self.limits[var].max_val is None
    def set_min(self, var, min_val):
        if var not in self.limits:
            self.limits[var] = Limit()
        self.limits[var].min_val = min_val
    def set_max(self, var, max_val):
        if var not in self.limits:
            self.limits[var] = Limit()
        self.limits[var].max_val = max_val
    def get_min(self, var):
        if var not in self.limits:
            return self.default_min
        min_val = self.limits[var].min_val
        return min_val if min_val is not None else self.default_min
    def get_max(self, var):
        if var not in self.limits:
            return self.default_max
        max_val = self.limits[var].max_val
        return max_val if max_val is not None else self.default_max
    def clone(self):
        cloned = VariableMap(self.default_min, self.default_max)
        for var, limit in self.limits.items():
            cloned.limits[var] = limit.clone()
        return cloned
    def pprint(self):
        lines = []
        for var in sorted(self.limits.keys()):
            limit = self.limits[var]
            lines.append(f'Variable {var} range [{limit.min_val}, {limit.max_val}]')
        return '\n'.join(lines)
