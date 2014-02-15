
import os
import sys

global COLORS_ENABLED

COLORS_ALWAYS_DISABLED = False
COLORS_ARE_BRIGHT = bool(os.getenv('COLORTERM'))

try:
    import colorama
    from colorama import Style as ColorStyle
    from colorama import Fore as ColorFore
except ImportError:
    COLORS_ALWAYS_DISABLED = True
    
    class BlankAll:
        init   = lambda : None
        deinit = lambda : None
        def __getattr__(self, name):
            return ''
            
    Fore = BlankAll()
    Style = BlankAll()
    colorama = BlankAll()
    

COLORS_ENABLED = (not COLORS_ALWAYS_DISABLED) and sys.stdout.isatty()
if COLORS_ENABLED:
    colorama.init()

if COLORS_ARE_BRIGHT:
    # not using the colorama color codes because they're too boring.
    COLOR_BLACK   = '\x1b[90m'
    COLOR_RED     = '\x1b[91m'
    COLOR_GREEN   = '\x1b[92m'
    COLOR_YELLOW  = '\x1b[93m'
    COLOR_BLUE    = '\x1b[94m'
    COLOR_MAGENTA = '\x1b[95m'
    COLOR_CYAN    = '\x1b[96m'
    COLOR_WHITE   = '\x1b[97m'
else:
    COLOR_BLACK   = ColorFore.BLACK
    COLOR_RED     = ColorFore.RED
    COLOR_GREEN   = ColorFore.GREEN
    COLOR_YELLOW  = ColorFore.YELLOW
    COLOR_BLUE    = ColorFore.BLUE
    COLOR_MAGENTA = ColorFore.MAGENTA
    COLOR_CYAN    = ColorFore.CYAN
    COLOR_WHITE   = ColorFore.WHITE

COLOR_HEADER  =  COLOR_GREEN
COLOR_DEBUG   =  ColorStyle.DIM + COLOR_MAGENTA
COLOR_WARNING =  COLOR_YELLOW
COLOR_ERROR   =  COLOR_RED + ColorStyle.BRIGHT
COLOR_RESET   =  ColorFore.RESET + ColorStyle.RESET_ALL

def color_disable():
    global COLORS_ENABLED
    COLORS_ENABLED = False
    colorama.deinit()
    
def color_enable():
    global COLORS_ENABLED
    COLORS_ENABLED = True
    colorama.reinit()

def printcolor(*args, **kwargs):
    color = kwargs.pop('color')
    if COLORS_ENABLED:
        args = list(args)
        args[0] = color + str(args[0])
        args[-1] = str(args[-1]) + COLOR_RESET
    print(*args, **kwargs)

def printwarn(*args, **kwargs):
    kwargs['color'] = COLOR_WARNING
    printcolor(*args, **kwargs)

def printheader(*args, **kwargs):
    kwargs['color'] = COLOR_HEADER
    printcolor(*args, **kwargs)

def printerror(*args, **kwargs):
    kwargs['color'] = COLOR_ERROR
    kwargs['file'] = sys.stderr
    printcolor(*args, **kwargs)

def printblue(*args, **kwargs):
    kwargs['color'] = '\x1b[94m'
    printcolor(*args, **kwargs)

def printgreen(*args, **kwargs):
    kwargs['color'] = ColorFore.GREEN
    printcolor(*args, **kwargs)

def printcyan(*args, **kwargs):
    kwargs['color'] = ColorFore.CYAN
    printcolor(*args, **kwargs)

def printdebug(*args, **kwargs):
    kwargs['color'] = COLOR_DEBUG
    printcolor(*args, **kwargs)

printelementname = printblue

