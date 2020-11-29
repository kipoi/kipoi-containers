import pytest

def pytest_addoption(parser):
    ''' attaches optional cmd-line args to the pytest machinery '''
    parser.addoption("--model", action="append", default=[], help="model name")
    
