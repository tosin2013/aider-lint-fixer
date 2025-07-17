#!/usr/bin/env python3
# Large problematic Python file for testing scalability

import datetime
import json
import requests

def bad_function_1(x,y,z):
    """Function with many issues"""
    if x==None:
        return
    result = x + y + z + 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 + 15 + 16 + 17 + 18 + 19 + 20
    try:
        result = result / 0
    except:
        pass
    return result

def bad_function_2(a,b,c,d,e):
    if a==None or b==None or c==None:
        return False
    long_line = a + b + c + d + e + "this is a very long string that exceeds the line length limit and should be broken into multiple lines"
    return long_line

class badClass1:
    def __init__(self,name,age,email):
        self.name=name
        self.age=age
        self.email=email
        
    def method_with_issues(self,x,y,z):
        if self.name==None:
            return False
        message = "Hello %s, you are %d years old" % (self.name, self.age)
        return True

class badClass2:
    def __init__(self,data):
        self.data=data
        
    def process_data(self,items=[]):
        items.append("bad")
        if self.data==None:
            return []
        result = []
        for item in self.data:
            if item is not None:
                result.append(item.upper())
        return result

def function_with_many_params(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p):
    if a==None or b==None or c==None or d==None:
        return None
    very_long_calculation = a + b + c + d + e + f + g + h + i + j + k + l + m + n + o + p + 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10
    return very_long_calculation

def another_bad_function(data):
    if data == None:
        return []
    try:
        result = json.loads(data)
    except:
        return {}
    return result

def function_with_unused_imports():
    # Uses only some of the imports
    current_time = datetime.datetime.now()
    return current_time

def function_with_bad_formatting(x,y):
    if x==None:return None
    result=x+y
    return result

def function_with_complex_logic(data,options,config):
    if data==None or options==None or config==None:
        return False
    
    # Complex nested logic with many issues
    for item in data:
        if item is not None:
            if "key" in item:
                if item["key"] == "value":
                    if options.get("process", False):
                        if config.get("enabled", True):
                            try:
                                result = item["key"].upper()
                            except:
                                continue
                            
    return True

def function_with_string_issues():
    message1 = "This is a string with 'single quotes' inside"
    message2 = 'This is a string with "double quotes" inside'
    long_string = "This is a very long string that should be broken into multiple lines because it exceeds the recommended line length limit"
    return message1 + message2 + long_string

def function_with_list_comprehension_issues(data):
    if data == None:
        return []
    
    # Could be simplified
    result = []
    for item in data:
        if item is not None:
            if len(item) > 0:
                result.append(item.strip().upper())
    
    return result

def function_with_dict_issues():
    # Missing spaces around operators
    data = {"key1":"value1","key2":"value2","key3":"value3"}
    
    # Bad comparison
    if data.get("key1")==None:
        return {}
    
    return data

def function_with_import_issues():
    # Unused imports at top of file
    # Using requests without importing it properly
    try:
        response = requests.get("http://example.com")
        return response.json()
    except:
        return {}

def function_with_variable_naming_issues():
    MyVariable = "bad naming"
    another_Variable = "also bad"
    CONSTANT_that_should_be_lowercase = "wrong"
    
    return MyVariable + another_Variable + CONSTANT_that_should_be_lowercase

def function_with_whitespace_issues():
    x=1
    y=2
    z=x+y
    
    if x==1:
        print("x is 1")
    
    return z

def function_with_docstring_issues(param1, param2):
    # Missing docstring
    if param1==None:
        return param2
    return param1 + param2

def function_with_exception_issues():
    try:
        result = 1 / 0
    except:
        pass
    
    try:
        data = json.loads("invalid json")
    except Exception as e:
        pass
    
    return None

# Global variables (bad practice)
GLOBAL_VAR1 = "bad practice"
global_var2 = "also bad"

# Missing main guard
print("This should be in a main guard")
bad_function_1(1, 2, 3)
function_with_many_params(1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16)
