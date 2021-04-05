class Range:
    def __init__(self, min_val=None, max_val=None):
        self.min_val = min_val
        self.max_val = max_val
    def clone(self):
        return Range(self.min_val, self.max_val)

# TODO: consolidate different type of maps
# Maybe:
#   var_map = VariableMap()
#   var_map.add_int_range('x', 0, 10)
#   var_map.add_float_range('x', 0.0, 10.0)
#   var_map.add_list('x', ['float', 'int'])
class VariableMap:
    def __init__(self, default_min=0, default_max=999):
        self.default_min = default_min
        self.default_max = default_max
        self.ranges = {}
    def remove_var(self, var):
        if var in self.ranges:
            self.ranges.pop(var)
    def has_range(self, var):
        return self.has_min(var) and self.has_max(var)
    def get_range(self, var):
        return (self.get_min(var), self.get_max(var))
    def set_range(self, var, min_val, max_val):
        self.set_min(var, min_val)
        self.set_max(var, max_val)
    def set_value(self, var, val):
        self.set_range(var, val, val)
    def is_range(self, var):
        assert(var in self.ranges)
        r = self.ranges[var]
        return r.min_val != r.max_val
    def is_value(self, var):
        assert(var in self.ranges)
        r = self.ranges[var]
        return r.min_val == r.max_val
    def has_min(self, var):
        return var in self.ranges and not self.ranges[var].min_val is None
    def has_max(self, var):
        return var in self.ranges and not self.ranges[var].max_val is None
    def set_min(self, var, min_val):
        if var not in self.ranges:
            self.ranges[var] = Range()
        self.ranges[var].min_val = min_val
    def set_max(self, var, max_val):
        if var not in self.ranges:
            self.ranges[var] = Range()
        self.ranges[var].max_val = max_val
    def get_min(self, var):
        if var not in self.ranges:
            return self.default_min
        min_val = self.ranges[var].min_val
        return min_val if min_val is not None else self.default_min
    def get_max(self, var):
        if var not in self.ranges:
            return self.default_max
        max_val = self.ranges[var].max_val
        return max_val if max_val is not None else self.default_max
    def clone(self):
        cloned = VariableMap(self.default_min, self.default_max)
        for var, limit in self.ranges.items():
            cloned.ranges[var] = limit.clone()
        return cloned
    def pprint(self):
        lines = []
        for var in sorted(self.ranges.keys()):
            limit = self.ranges[var]
            lines.append(f'Variable {var} range [{limit.min_val}, {limit.max_val}]')
        return '\n'.join(lines)
