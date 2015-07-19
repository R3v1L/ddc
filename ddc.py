#!/usr/bin/python -OO
# -*- coding: utf-8 -*-
###############################################################################
# Author: (C) Oliver Gutiérrez
# Module: ddc
# Description: Django Development Console application
###############################################################################

# Import application class
from ddclib import EVOGTKApp

DEBUG=True

#===========================================================================
# Application start
#===========================================================================
if __name__=='__main__':
    # Start application
    EVOGTKApp(guifiles=['gui.ui'],debug=DEBUG).run()

