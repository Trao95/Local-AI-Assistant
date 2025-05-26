"""
This script applies the chat interface fixes to prevent user messages from disappearing.
Run this script instead of personalassistant.py to use the fixed version.
"""

import sys
import importlib.util

# First, import the fixed chat interface
spec = importlib.util.spec_from_file_location("fixed_chat", "fixed_chat.py")
fixed_chat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixed_chat)

# Now import and run the original application
spec = importlib.util.spec_from_file_location("personalassistant", "personalassistant.py")
personalassistant = importlib.util.module_from_spec(spec)

# Override the original ChatInterface.__init__ to apply our fixes
original_chat_interface_init = personalassistant.ChatInterface.__init__

def patched_chat_interface_init(self, parent, toggle_theme_callback):
    # Call the original __init__
    original_chat_interface_init(self, parent, toggle_theme_callback)
    # Apply our fixes
    fixed_chat.FixedChatInterface.fix_chat_interface(self)
    print("Applied chat interface fixes to prevent user messages from disappearing")

# Apply the patch
personalassistant.ChatInterface.__init__ = patched_chat_interface_init

# Run the application
spec.loader.exec_module(personalassistant)
