# encoding: utf-8
#
# Copyright (c) 2017 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2017-12-20
#

"""Put multiple data formats on the macOS pasteboard at the same time."""

from __future__ import print_function, absolute_import

import logging

from workflow.util import run_trigger
log = logging.getLogger(__name__)

# Try to import macOS-specific modules, fall back gracefully if not available
try:
    from AppKit import NSPasteboard
    from Foundation import NSData
    HAS_APPKIT = True
except ImportError:
    HAS_APPKIT = False
    log.warning("AppKit not available - clipboard functionality will be limited")

# Some common UTIs
UTI_HTML = 'public.html'
UTI_TEXT = 'public.rtf'
UTI_PLAIN = 'public.utf8-plain-text'
UTI_URL = 'public.url'
UTI_URL_NAME = 'public.url-name'

# JXA script to simulate CMD+V keypress via Carbon.
# Unaffected by other modifiers the user may be holding down, unlike
# System Events.
PASTE_SCRIPT = """
ObjC.import('Carbon');

var source = $.CGEventSourceCreate($.kCGEventSourceStateCombinedSessionState);

var pasteCommandDown = $.CGEventCreateKeyboardEvent(source, $.kVK_ANSI_V, true);
$.CGEventSetFlags(pasteCommandDown, $.kCGEventFlagMaskCommand);
var pasteCommandUp = $.CGEventCreateKeyboardEvent(source, $.kVK_ANSI_V, false);

$.CGEventPost($.kCGAnnotatedSessionEventTap, pasteCommandDown);
$.CGEventPost($.kCGAnnotatedSessionEventTap, pasteCommandUp);

"""


def nsdata(s):
    """Return an NSData instance for string `s`."""
    if isinstance(s, str):
         s = s.encode('utf-8')
    else:
        s = str(s)
    log.debug ("str s is: %s" % s)
    return NSData.dataWithBytes_length_(s, len(s))


def set(contents):
    """Set the clipboard contents.

    `contents` should have the format:

        {
            'UTI': 'value',
            ...
        }

        e.g. `{'public.html': '<a href="...">...</a>'}`

    Each value must be a `unicode` or `str()`-able object.

    """
    if not HAS_APPKIT:
        log.warning("Cannot set clipboard - AppKit not available")
        return False
        
    for uti in contents:
        log.debug("uti: %s, has_content=%s", uti, contents[uti] is not None)

    pboard = NSPasteboard.generalPasteboard()
    pboard.clearContents()
    for uti, value in contents.items():
        data = nsdata(value)
        # PyObjC expects a Python str for type
        pboard.setData_forType_(data, str(uti))
    return True


def paste():
    """Simulate CMD+V to paste clipboard."""
    run_trigger('paste')
    # This doesn't appear to work on Catalina :(
    # run_jxa(PASTE_SCRIPT)


def clear():
    """Clear the clipboard."""
    if not HAS_APPKIT:
        log.warning("Cannot clear clipboard - AppKit not available")
        return False
        
    pboard = NSPasteboard.generalPasteboard()
    pboard.clearContents()
    return True


def get_string(uti=UTI_PLAIN):
    """Return string content for the given UTI, if available."""
    if not HAS_APPKIT:
        log.warning("Cannot read clipboard - AppKit not available")
        return None
        
    pboard = NSPasteboard.generalPasteboard()
    try:
        s = pboard.stringForType_(str(uti))
        return str(s) if s is not None else None
    except Exception:  # pragma: no cover
        return None


