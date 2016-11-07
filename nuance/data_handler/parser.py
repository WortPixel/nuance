#!/usr/bin/env python
# coding: utf-8

def check_type(arg, dtype, name=None, default=None):
    ''' Check if arg is of type dtype
        
        Args:
            arg: Argument to check
            dtype: Desired type of arg
            name: Name of the provided argument
            default: Default value to return if problems occure

        Returns:
            Arg if type is correct

        Raises:
            TypeError is type(arg) != dtype
    '''
    if arg is not None:
        if isinstance(arg, dtype):
            return arg
        else:
            try:
                return dtype(arg)   
            except:
                if name is not None:
                    raise TypeError('{} needs to be of type {}.'.format(name, dtype))
                return default
    else:
        return default


def is_ending_in(ending_list, filelist):
    if isinstance(ending_list, list):
        return all(any([filename.endswith(ending) for ending in ending_list]) \
                   for filename in filelist)
    else:
        raise TypeError("ending_list needs to be of type list, and filename needs to be of type str.")
