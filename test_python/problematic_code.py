#!/usr/bin/env python3
# Problematic Python code for testing linters


def bad_function(x, y, z):
    """This function has many issues"""
    if x is None:
        return
    
    # Long line that exceeds PEP 8 recommendations and should be split into multiple lines for better readability
    result = (
        x + y + z + 1 + 2 + 3 + 4 + 5 + 6 + 7 +
        8 + 9 + 10 + 11 + 12 + 13 + 14 + 15
    )
    
    # Missing type hints
    def inner_function(a, b):
        return a + b
    
    # Bare except
    try:
        result = inner_function(x, y)
    except Exception:
        pass
    
    # Mutable default argument
    def another_bad_function(items=[]):
        items.append("bad")
        return items
    
    # Missing return type annotation
    return result



class badClass:
    """Class with naming issues"""
    
    def __init__(self, name):
        self.name = name
        
    def method_with_issues(self,x,y):
        # No docstring
        # Comparison with None using ==
        if self.name is None:
            return False
            
        # String formatting issues
        _ = "Hello %s, you have %d items" % (self.name, x)
        
        return True


# Global variable (not recommended)
GLOBAL_VAR = "bad practice"




# Function without type hints
def process_data(data):
    if data is None:
        return []
    
    # List comprehension that could be simplified
    result = []
    for item in data:
        if item is not None:
            result.append(item.upper())
    
    return result

# Missing main guard
print("This should be in a main guard")
bad_function(1, 2, 3)
