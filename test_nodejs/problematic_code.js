// Problematic Node.js code for testing linters

var fs = require('fs');
var path = require('path');
var http = require('http');
var express = require('express');

function badFunction(x,y,z) {
    if (x == null) {
        return;
    }
    
    var unused_var = "this is not used";
    
    // Long line that exceeds recommended length and should be split into multiple lines for better readability and maintainability
    var result = x + y + z + 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 + 15 + 16 + 17 + 18 + 19 + 20;
    
    // Missing semicolon
    var data = {key: "value", another_key:"another_value"}
    
    // Bad comparison
    if (result == undefined) {
        console.log("result is undefined")
    }
    
    // Inconsistent quotes
    var message1 = "Hello world";
    var message2 = 'Hello world';
    
    return result
}

class BadClass {
    constructor(name,age) {
        this.name=name;
        this.age=age;
    }
    
    methodWithIssues(x,y) {
        // No var/let/const
        globalVar = "bad practice";
        
        // Eval usage (dangerous)
        eval("console.log('bad practice')");
        
        // == instead of ===
        if (this.name == null) {
            return false;
        }
        
        // Missing return
        var result = x + y;
    }
}

// Function without proper error handling
function processData(data) {
    if (data == null) {
        return [];
    }
    
    try {
        var parsed = JSON.parse(data);
    } catch (e) {
        // Empty catch block
    }
    
    return parsed;
}

// Callback hell
function nestedCallbacks(callback) {
    fs.readFile('file1.txt', function(err, data1) {
        if (err) throw err;
        fs.readFile('file2.txt', function(err, data2) {
            if (err) throw err;
            fs.readFile('file3.txt', function(err, data3) {
                if (err) throw err;
                callback(data1 + data2 + data3);
            });
        });
    });
}

// Missing 'use strict'
function oldStyleFunction() {
    arguments.callee; // Deprecated
    with (Math) { // Deprecated
        var x = cos(PI);
    }
}

// Inconsistent spacing and formatting
var obj={key1:"value1",key2:"value2"};
var arr=[1,2,3,4,5];

// Missing error handling in async operations
http.get('http://example.com', function(res) {
    res.on('data', function(chunk) {
        console.log(chunk);
    });
});

// Global variables
var GLOBAL_VAR = "bad practice";
window.globalVar = "also bad";

// Console.log left in code
console.log("Debug message that should be removed");

// Unreachable code
function unreachableCode() {
    return true;
    console.log("This will never execute");
}

// Missing JSDoc
function complexFunction(param1, param2, param3) {
    return param1 * param2 + param3;
}

// Prototype pollution vulnerability
Object.prototype.isAdmin = true;

// Using deprecated Buffer constructor
var buffer = new Buffer('hello');

// Missing await
async function asyncFunction() {
    Promise.resolve('hello');
    return 'done';
}

// Export at the end (should be at top)
module.exports = {
    badFunction: badFunction,
    BadClass: BadClass,
    processData: processData
};
