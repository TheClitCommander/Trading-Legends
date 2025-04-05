#!/usr/bin/env python3
"""
Wrapper script to run the map editor with extra debug information
"""

import os
import sys
import traceback

# Set the right video driver for Mac
os.environ['SDL_VIDEODRIVER'] = 'cocoa'
print("Set SDL_VIDEODRIVER to cocoa for Mac")

try:
    print("Starting map editor initialization...")
    # Import and run the map editor
    import map_editor_main
    print("Imported map editor module")
    
    # Explicitly create an instance and run it
    print("Creating editor instance...")
    from map_editor_main import StandaloneMapEditorCore, SUBCATEGORIES
    print("Creating editor with asset categories from previous implementation...")
    editor = StandaloneMapEditorCore(SUBCATEGORIES, {})
    print("Starting editor main loop...")
    editor.run()
    
except Exception as e:
    print(f"ERROR running map editor: {e}")
    print("\nDetailed error information:")
    traceback.print_exc()
    
print("Editor execution completed")
