import os, errno
import json

from typing import Any, Callable

from dvrpsim.exceptions import RoutingError

#region IO functions

def write_jsonfile( data, filename_with_path:str ) -> None:
    """
    Writes the given JSON data to the given file.
    
    :param Any data:               JSON data
    :param str filename_with_path: file name with path
    """
    try:
        with open( filename_with_path, 'w' ) as jsonfile:
            json.dump( data, jsonfile, indent= 2 )

    except Exception as exc:
        raise Exception( f'could not write file "{filename_with_path}" due to {exc}' )

def read_jsonfile( filename_with_path:str ):
    """
    Return JSON data from the given file.
    
    :param str filename_with_path: file name with path
    """
    try:
        with open( filename_with_path, 'r' ) as jsonfile:
            return json.load( jsonfile )

    except Exception as exc:
        raise Exception( f'could not read file "{filename_with_path}" due to {exc}' )
    
def remove_file( filename_with_path:str ):
    """
    Removes the given file, if exists.
    
    :param str filename_with_path: file name with path
    """
    try:
        os.remove( filename_with_path )

    except FileNotFoundError:
        return
    
    except Exception as exc:
        raise Exception( f'could not remove file "{filename_with_path}" due to {exc}' )
    
def create_directory( dirname_with_path:str ):
    """
    Creates the given directory, if not exists.
    
    :param str dirname_with_path: directory name with path
    """
    try:
        os.makedirs( dirname_with_path )
    
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise Exception( f'could not create directory "{dirname_with_path}" due to {exc}' )

#endregion

#region Main functions

def call_module_function( module_name:str, function_name:str, *args, **kwargs ) -> Any:
    """
    Invokes the given function with the given parameters located in the given module.

    :param str module_name:   name of the python module
    :param str function_name: name of the routing function
    :param Any args:          arguments for the routing function
    :param Any kwargs:        keyword arguments for the routing function

    :return: the return value, if any, of the routing function
    """
    import importlib

    try:
        routing_modul    = importlib.import_module( module_name )
        routing_function = getattr( routing_modul, function_name )
        return routing_function( *args, **kwargs )

    except Exception as exc:
        raise RoutingError( f'external (python) routing algorithm: {exc}' )

def call_algorithm_in_subprocess( algorithm_calling_command, max_seconds:float= None ):
    """
    
    """
    import subprocess

    proc = subprocess.Popen( algorithm_calling_command, stdout= subprocess.PIPE )

    try:
        _ = proc.communicate()
        _ = proc.wait( timeout= max_seconds )

    except Exception as exc:
        raise RoutingError( f'external (subprocess) routing algorithm: {exc}' )

def file_based_routing_via_direct_function_call( state:dict, state_filename:str, decision_filename:str, routing_function:Callable, *args, **kwargs ) -> Any:
    """
    File-based routing via direct function call.

    Main steps:
        1. Remove old decison file, if any.
        2. Write the given state to file.
        3. Call the given routing function with the given arguments.
        4. Read the resulted decision file, and return the decision.

    :param dict     state:             state
    :param str      state_filename:    state filename with path
    :param str      decision_filename: decision filename with path
    :param Callable routing_function:  routing function
    :param Any      args:              arguments for the routing function
    :param Any      kwargs:            keyword arguments for the routing function

    :return: decision
    """
    # delete old decision file, if any
    remove_file( decision_filename )

    # write state file
    write_jsonfile( state, state_filename )

    # call routing function
    try:
        routing_function( *args, **kwargs )

    except Exception as exc:
        raise RoutingError( f'direct routing: {exc}' )

    # read decision
    decision = read_jsonfile( decision_filename )

    return decision

def file_based_routing_via_module_function_call( state:dict, state_filename:str, decision_filename:str, module_name:str, function_name:str, *args, **kwargs ) -> Any:
    """
    File-based routing via module function call.

    Main steps:
        1. Remove old decison file, if any.
        2. Write the given state to file.
        3. Call the given routing function with the given arguments.
        4. Read the resulted decision file, and return the decision.

    :param dict state:             state
    :param str  state_filename:    state filename with path
    :param str  decision_filename: decision filename with path
    :param str  module_name:       module name
    :param str  function_name:     routing function
    :param Any  args:              arguments for the routing function
    :param Any  kwargs:            keyword arguments for the routing function

    :return: decision
    """    
    # delete old decision file, if any
    remove_file( decision_filename )

    # write state file
    write_jsonfile( state, state_filename )

    # call routing algorithm
    _ = call_module_function( module_name, function_name, *args, **kwargs )

    # read decision
    decision = read_jsonfile( decision_filename )

    return decision
    
def file_based_routing_via_subprocess( state:dict, state_filename_with_path:str, decision_filename_with_path:str, algorithm_calling_command, max_seconds:float= None ) -> Any:
    """
    File-based routing via subprocess.

    Main steps:
        1. Remove old decison file, if any.
        2. Write the given state to file.
        3. Execute the given command in a subprocess.
        4. Read the resulted decision file, and return the decision.

    :param dict  state:                     state
    :param str   state_filename:            state filename with path
    :param str   decision_filename:         decision filename with path
    :param str   algorithm_calling_command: algorithm calling command
    :param float max_seconds:               max time

    :return: decision
    """
    # delete old decision file, if any
    remove_file( decision_filename_with_path )

    # write state file
    write_jsonfile( state, state_filename_with_path )

    # call external algorithm
    call_algorithm_in_subprocess( algorithm_calling_command, max_seconds )

    # read decision
    decision = read_jsonfile( decision_filename_with_path )

    return decision

#endregion
