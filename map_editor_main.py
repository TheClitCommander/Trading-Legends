#!/usr/bin/env python3
"""
Trading Legends Standalone Map Editor (FIXED VERSION)

A visual editor for creating and modifying maps for the Trading Legends game.
This standalone version doesn't require importing from the existing code structure.

This version includes fixes for texture scaling issues to ensure all textures
are consistently scaled to match the defined TILE_SIZE.
"""
import os
import sys
import pygame
import json
import random
import math
import re
from pygame.locals import *

# Initialize pygame
pygame.init()
pygame.font.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SIDEBAR_WIDTH = 300
TILE_SIZE = 32
FPS = 60
GRID_COLOR = (100, 100, 100, 100)
BACKGROUND_COLOR = (40, 40, 40)

class StandaloneMapEditor:
    """Standalone map editor that doesn't rely on importing Trading Legends modules"""
    
    def __init__(self):
        """Initialize the map editor"""
        print("\n=== Trading Legends Standalone Map Editor ===\n")
        
        # Initialize pygame
        pygame.init()
        
        # Setup display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Trading Legends Map Editor")
        
        # Setup clock
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Map state
        self.map_data = {}
        self.map_layers = ["terrain", "vegetation", "buildings", "decorations", "npcs"]
        self.current_layer = "terrain"
        self.hidden_layers = []  # Layers that are currently hidden
        
        # Editor state
        self.camera_x = 0
        self.camera_y = 0
        self.grid_enabled = True
        self.show_sidebar = True
        self.selected_category = "terrain"
        self.selected_tile = "grass"
        self.selected_tile_data = None  # Store the actual texture data of selected tile
        
        # Sidebar scroll state
        self.sidebar_scroll = 0
        self.sidebar_scroll_max = 0
        self.sidebar_tile_scroll = 0
        self.sidebar_tile_scroll_max = 0
        self.tiles_per_page = 20  # Adjust based on screen size
        
        # Asset groups - store groups of related assets
        self.asset_groups = {}
        
        # UI elements
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 18)
        
        # Define available tile types and colors
        self.categories = {
            "terrain": ["grass", "dirt", "sand", "water", "stone"],
            "vegetation": ["tree", "bush", "flower", "plant"],
            "buildings": ["house", "shrine", "shop", "market"],
            "npcs": ["villager", "merchant", "guard", "elder"],
            "decorations": ["fence", "barrel", "sign", "rock"]
        }
        
        # Tile colors for rendering
        self.tile_colors = {
            # Terrain
            "grass": (76, 153, 47),
            "dirt": (155, 118, 83),
            "sand": (255, 235, 156),
            "water": (52, 152, 219),
            "stone": (127, 140, 141),
            # Vegetation
            "tree": (30, 130, 30),
            "bush": (40, 180, 40),
            "flower": (255, 100, 100),
            "plant": (50, 200, 50),
            # Buildings
            "house": (184, 134, 11),
            "shrine": (120, 60, 0),
            "shop": (205, 92, 92),
            "market": (205, 133, 63),
            # NPCs
            "villager": (230, 126, 34),
            "merchant": (241, 196, 15),
            "guard": (52, 73, 94),
            "elder": (142, 68, 173),
            # Decorations
            "fence": (139, 69, 19),
            "barrel": (160, 82, 45),
            "sign": (230, 230, 230),
            "rock": (128, 128, 128)
        }
        
        # Initialize map
        self.initialize_new_map(40, 30)
        
        # Try to load assets
        self.textures = self.scan_project_assets()
        
        print("\n✅ Map Editor initialized successfully!")
        print("Use arrow keys or WASD to navigate")
        print("G to toggle grid, Ctrl+S to save, Ctrl+L to load")
        print("Click on sidebar to select tiles, click on map to place them")
    
    def slice_tilesheet(self, image, tile_size=32):
        """Slice a tilesheet into individual tiles
        Returns a list of pygame surfaces, each representing a tile
        """
        tiles = []
        width, height = image.get_size()
        
        # Skip tiny images
        if width < tile_size or height < tile_size:
            return [image]  # Return the original as a single tile
            
        # Handle large single images that might not be tilesets
        if width <= 64 and height <= 64:
            return [image]  # Likely a single image
            
        # For larger images, determine if this is likely a tileset
        is_tileset = False
        
        # Check if dimensions are multiples of common tile sizes
        for size in [16, 24, 32, 48, 64]:
            if width % size == 0 and height % size == 0:
                tile_size = size
                is_tileset = True
                break
        
        # If not a clear tileset, return as single image
        if not is_tileset:
            return [image]
        
        # Slice the tileset into individual tiles
        print(f"Slicing tileset: {width}x{height} into {tile_size}x{tile_size} tiles")
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                if x + tile_size <= width and y + tile_size <= height:
                    # Create a rectangle for this tile
                    rect = pygame.Rect(x, y, tile_size, tile_size)
                    
                    # Extract the tile as a new surface
                    try:
                        tile = image.subsurface(rect).copy()
                        tiles.append(tile)
                    except ValueError as e:
                        print(f"Error slicing tile at {x},{y}: {e}")
        
        print(f"Extracted {len(tiles)} tiles from tileset")
        return tiles
    
    def scan_project_assets(self):
        """Scan the project directory for assets"""
        print("\n🔍 Scanning for assets...")
        
        textures = {}
        
        # Initialize categories
        for category in self.categories:
            textures[category] = {}
        
        # Define possible asset directories and high-quality paths from memory
        asset_dirs = [
            "asset_packs",
            "src/assets",
            "assets"
        ]
        
        # List of known high-quality assets to prioritize based on memory
        known_assets = [
            "asset_packs/extracted_assets/Ninja Adventure - Asset Pack/Tilesets/TilesetHouse.png",
            "asset_packs/extracted_assets/mystic_woods_free_2.2/sprites/tilesets/walls/walls.png",
            "asset_packs/extracted_assets/Cute_Fantasy_Fre/Tiles/Market_Stalls.png",
            "asset_packs/extracted_assets/mystic_woods_free_2.2/sprites/objects"
        ]
        
        # Paths that are definitely tilesets and should be sliced
        tileset_paths = [
            "Tilesets", "tileset", "tiles", "walls", "Market_Stalls"
        ]
        
        assets_found = 0
        sliced_tilesets = 0
        
        # First process known high-quality assets
        for asset_path in known_assets:
            full_path = os.path.join(os.getcwd(), asset_path)
            
            # Handle directory paths
            if os.path.isdir(full_path):
                for root, _, files in os.walk(full_path):
                    for file in [f for f in files if f.lower().endswith(('.png', '.jpg'))]:                       
                        filepath = os.path.join(root, file)
                        self._process_asset_file(filepath, textures, tileset_paths)
                        assets_found += 1
            
            # Handle file paths
            elif os.path.isfile(full_path) and full_path.lower().endswith(('.png', '.jpg')):
                self._process_asset_file(full_path, textures, tileset_paths)
                assets_found += 1
        
        # Then look for additional assets in standard directories
        for base_dir in asset_dirs:
            base_path = os.path.join(os.getcwd(), base_dir)
            
            if not os.path.exists(base_path):
                continue
                
            print(f"  Scanning {base_dir}...")
            
            # Walk through directories
            for root, _, files in os.walk(base_path):
                # Skip already processed directories
                if any(known in root for known in known_assets if isinstance(known, str) and os.path.isdir(os.path.join(os.getcwd(), known))):
                    continue
                    
                # Only look at png/jpg files
                image_files = [f for f in files if f.lower().endswith(('.png', '.jpg'))]
                
                if not image_files:
                    continue
                
                # Try to determine category from path
                path_lower = root.lower()
                category = None
                
                # Check for category indicators in path
                if any(kw in path_lower for kw in ["tile", "terrain", "ground"]):
                    category = "terrain"
                elif any(kw in path_lower for kw in ["tree", "bush", "plant", "nature"]):
                    category = "vegetation"
                elif any(kw in path_lower for kw in ["build", "house", "structure"]):
                    category = "buildings"
                elif any(kw in path_lower for kw in ["character", "npc", "people"]):
                    category = "npcs"
                elif any(kw in path_lower for kw in ["item", "prop", "decoration"]):
                    category = "decorations"
                
                # If we found a category, process the assets
                if category:
                    # Process a limited number of images per directory
                    for img_file in image_files[:5]:
                        filepath = os.path.join(root, img_file)
                        self._process_asset_file(filepath, textures, tileset_paths, category)
                        assets_found += 1
        
        print(f"✅ Loaded {assets_found} assets with {sliced_tilesets} sliced tilesets")
        return textures
    
    def _process_asset_file(self, filepath, textures, tileset_paths, default_category=None):
        """Process a single asset file"""
        try:
            # Determine the basename and filename
            filename = os.path.basename(filepath)
            name_without_ext = os.path.splitext(filename)[0].lower()
            path_lower = filepath.lower()
            
            # Debug sizing
            print(f"Processing asset: {filename} for TILE_SIZE: {TILE_SIZE}px")
            
            # Determine category based on path or default
            category = default_category
            if not category:
                if any(kw in path_lower for kw in ["tile", "terrain", "ground"]):
                    category = "terrain"
                elif any(kw in path_lower for kw in ["tree", "bush", "plant", "nature"]):
                    category = "vegetation"
                elif any(kw in path_lower for kw in ["build", "house", "structure"]):
                    category = "buildings"
                elif any(kw in path_lower for kw in ["character", "npc", "people"]):
                    category = "npcs"
                elif any(kw in path_lower for kw in ["item", "prop", "decoration"]):
                    category = "decorations"
                else:
                    # Default to terrain if no category is found
                    category = "terrain"
            
            try:
                # Load the original texture
                orig_texture = pygame.image.load(filepath)
                
                # Group base name for related tiles (without numbers)
                base_group_name = re.sub(r'\d+', '', name_without_ext).strip('_')
                
                # Determine if this is a tileset that should be sliced
                is_tileset = any(ts in path_lower for ts in tileset_paths)
                width, height = orig_texture.get_size()
                print(f"  Original size: {width}x{height}")
                
                # Images larger than 64x64 are likely tilesets
                if (width > 64 and height > 64) or is_tileset:
                    # Slice the tileset
                    tile_surfaces = self.slice_tilesheet(orig_texture)
                    
                    # Create a group for these tiles
                    if base_group_name not in self.asset_groups:
                        self.asset_groups[base_group_name] = {
                            "category": category,
                            "tiles": [],
                            "preview": tile_surfaces[0] if tile_surfaces else None
                        }
                    
                    # Add each tile as a separate entry
                    for i, tile_surface in enumerate(tile_surfaces):
                        tile_type = f"{name_without_ext}_{i+1}"
                        
                        # Add this tile to its group
                        if tile_type not in self.asset_groups[base_group_name]["tiles"]:
                            self.asset_groups[base_group_name]["tiles"].append(tile_type)
                        
                        # Add to category if not exists
                        if tile_type not in self.categories[category]:
                            self.categories[category].append(tile_type)
                            # Assign a random color for fallback
                            self.tile_colors[tile_type] = (
                                random.randint(100, 200),
                                random.randint(100, 200),
                                random.randint(100, 200)
                            )
                        
                        # Get original size before scaling
                        ts_width, ts_height = tile_surface.get_size()
                        
                        # Scale the tile to match TILE_SIZE if needed
                        if ts_width != TILE_SIZE or ts_height != TILE_SIZE:
                            scaled_tile = pygame.transform.scale(tile_surface, (TILE_SIZE, TILE_SIZE))
                        else:
                            scaled_tile = tile_surface
                        
                        # Store the tile with group information and original size
                        textures[category][tile_type] = {
                            "texture": scaled_tile,
                            "path": filepath,
                            "tileset_index": i,
                            "is_sliced": True,
                            "group": base_group_name,
                            "original_size": (ts_width, ts_height)
                        }
                else:
                    # Single image processing
                    # Convert for better performance, but only if the image doesn't use alpha
                    if "png" in path_lower or "gif" in path_lower:
                        texture = orig_texture.convert_alpha()
                    else:
                        texture = orig_texture.convert()
                    
                    # Try to match with a known tile type
                    tile_type = None
                    for t in self.categories[category]:
                        if t in name_without_ext:
                            tile_type = t
                            break
                    
                    # Use the first part of the filename if no match
                    if not tile_type:
                        tile_type = name_without_ext.split('_')[0]
                        
                        # Add this new tile type to the category
                        if tile_type not in self.categories[category]:
                            self.categories[category].append(tile_type)
                            self.tile_colors[tile_type] = (
                                random.randint(100, 200),
                                random.randint(100, 200),
                                random.randint(100, 200)
                            )
                    
                    # Add to group if it seems related to other tiles
                    if base_group_name not in self.asset_groups:
                        self.asset_groups[base_group_name] = {
                            "category": category,
                            "tiles": [tile_type],
                            "preview": texture
                        }
                    elif tile_type not in self.asset_groups[base_group_name]["tiles"]:
                        self.asset_groups[base_group_name]["tiles"].append(tile_type)
                    
                    # Get dimensions for original texture
                    orig_width, orig_height = texture.get_size()
                    print(f"  Original size: {orig_width}x{orig_height}")
                    
                    # Always scale the image to match the tile size for consistent proportions
                    scaled_texture = pygame.transform.scale(texture, (TILE_SIZE, TILE_SIZE))
                    
                    # Store the scaled image with original dimensions
                    textures[category][tile_type] = {
                        "texture": scaled_texture,
                        "path": filepath,
                        "is_sliced": False,
                        "group": base_group_name,
                        "original_size": (orig_width, orig_height)
                    }
                    
            except pygame.error as e:
                print(f"  ⚠️ Error loading {filepath}: {e}")
            except Exception as e:
                print(f"  ⚠️ Error processing {filepath}: {e}")
                
                # Add to group if it seems related to other tiles
                base_group_name = name_without_ext.split('_')[0]
                if base_group_name not in self.asset_groups:
                    self.asset_groups[base_group_name] = {
                        "category": category,
                        "tiles": [tile_type],
                        "preview": texture
                    }
                elif tile_type not in self.asset_groups[base_group_name]["tiles"]:
                    self.asset_groups[base_group_name]["tiles"].append(tile_type)
                
                # Get dimensions for debugging
                tex_width, tex_height = texture.get_size()
                print(f"  Storing texture: {tile_type} ({tex_width}x{tex_height})")
                
                # Scale the texture to match the tile size - this ensures proportional art
                if tex_width != TILE_SIZE or tex_height != TILE_SIZE:
                    scaled_texture = pygame.transform.scale(texture, (TILE_SIZE, TILE_SIZE))
                    texture = scaled_texture
                
                # Store the texture with group information
                textures[category][tile_type] = {
                    "texture": texture,
                    "path": filepath,
                    "is_sliced": False,
                    "group": base_group_name,
                    "original_size": (tex_width, tex_height)
                }
                
        except pygame.error as e:
            print(f"  ⚠️ Error loading {filepath}: {e}")
        except Exception as e:
            print(f"  ⚠️ Error processing {filepath}: {e}")

    
    def initialize_new_map(self, width, height):
        """Initialize a new empty map"""
        self.map_data = {
            "name": "New Map",
            "width": width,
            "height": height,
            "tile_size": TILE_SIZE,
            "layers": {}
        }
        
        # Initialize empty layers
        for layer in self.map_layers:
            self.map_data["layers"][layer] = {}
    
    def run(self):
        """Main application loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            
            elif event.type == KEYDOWN:
                self.handle_key_press(event.key)
            
            elif event.type == MOUSEBUTTONDOWN:
                # Debug click position
                x, y = event.pos
                print(f"Mouse click at ({x}, {y}) with button {event.button}")
                
                # Mouse wheel scrolling for sidebar
                if event.button == 4:  # Scroll up
                    if pygame.mouse.get_pos()[0] < SIDEBAR_WIDTH:
                        self.sidebar_tile_scroll = max(0, self.sidebar_tile_scroll - 1)
                        print(f"Scroll up: {self.sidebar_tile_scroll}")
                elif event.button == 5:  # Scroll down
                    if pygame.mouse.get_pos()[0] < SIDEBAR_WIDTH:
                        self.sidebar_tile_scroll = min(self.sidebar_tile_scroll_max, self.sidebar_tile_scroll + 1)
                        print(f"Scroll down: {self.sidebar_tile_scroll}")
                else:
                    self.handle_mouse_click(event.pos, event.button)
    
    def handle_key_press(self, key):
        """Handle keyboard input"""
        # Navigation with arrow keys or WASD
        if key in [K_LEFT, K_a]:
            self.camera_x -= TILE_SIZE
        elif key in [K_RIGHT, K_d]:
            self.camera_x += TILE_SIZE
        elif key in [K_UP, K_w]:
            # If shift is held, scroll sidebar instead of camera
            if pygame.key.get_mods() & KMOD_SHIFT:
                self.sidebar_tile_scroll = max(0, self.sidebar_tile_scroll - 1)
            else:
                self.camera_y -= TILE_SIZE
        elif key in [K_DOWN, K_s]:
            # If shift is held, scroll sidebar instead of camera
            if pygame.key.get_mods() & KMOD_SHIFT:
                self.sidebar_tile_scroll = min(self.sidebar_tile_scroll_max, self.sidebar_tile_scroll + 1)
            else:
                self.camera_y += TILE_SIZE
        
        # Toggle grid
        elif key == K_g:
            self.grid_enabled = not self.grid_enabled
            print(f"Grid {'enabled' if self.grid_enabled else 'disabled'}")
        
        # Save map
        elif key == K_s and pygame.key.get_mods() & KMOD_CTRL:
            self.save_map()
        
        # Load map
        elif key == K_l and pygame.key.get_mods() & KMOD_CTRL:
            self.load_map()
        
        # Switch layers with number keys
        elif key == K_1:
            self.current_layer = "terrain"
        elif key == K_2:
            self.current_layer = "vegetation"
        elif key == K_3:
            self.current_layer = "buildings"
        elif key == K_4:
            self.current_layer = "decorations"
        elif key == K_5:
            self.current_layer = "npcs"
    
    def handle_mouse_click(self, pos, button):
        """Handle mouse input"""
        # Check if click is in sidebar
        if pos[0] < SIDEBAR_WIDTH:
            print(f"Handling sidebar click at {pos}")
            self.handle_sidebar_click(pos)
        else:
            # Place or remove tile on map
            map_x, map_y = self.screen_to_map(pos)
            print(f"Map coordinates: ({map_x}, {map_y})")
            
            if button == 1:  # Left click - place tile
                if self.selected_tile:
                    print(f"Attempting to place '{self.selected_tile}' at ({map_x}, {map_y})")
                    self.place_tile(map_x, map_y)
                else:
                    print("No tile selected for placement")
            elif button == 3:  # Right click - remove tile
                self.remove_tile(map_x, map_y)
    
    def handle_sidebar_click(self, pos):
        """Handle clicks on the sidebar UI"""
        # Category selection area
        category_height = 30
        category_y = 60
        
        # Check for category clicks
        for category in self.categories:
            category_rect = pygame.Rect(10, category_y, SIDEBAR_WIDTH - 20, 30)
            
            if category_rect.collidepoint(pos):
                # Update selected category and current layer
                self.selected_category = category
                self.current_layer = category
                # Reset tile scroll when changing categories
                self.sidebar_tile_scroll = 0
                
                # Set initial selected tile for this category
                if self.categories[category]:
                    self.selected_tile = self.categories[category][0]
                    # Store texture data for the selected tile
                    if category in self.textures and self.selected_tile in self.textures[category]:
                        self.selected_tile_data = self.textures[category][self.selected_tile]
                    else:
                        self.selected_tile_data = None
                else:
                    self.selected_tile = None
                    self.selected_tile_data = None
                
                print(f"Selected category: {category}, initial tile: {self.selected_tile}")
                return
            
            category_y += 35
        
        # If we get here, no category was clicked, check for tile clicks
        if not self.selected_category or not self.categories[self.selected_category]:
            return
            
        # Calculate tile display area starting position
        tiles_y = 60 + (35 * len(self.categories)) + 25  # Category headers + spacing
        tile_size = 40
        tiles_per_row = (SIDEBAR_WIDTH - 20) // tile_size
        
        # Calculate total rows needed and set max scroll
        total_tiles = len(self.categories[self.selected_category])
        visible_rows = (SCREEN_HEIGHT - tiles_y - 120) // tile_size
        total_rows = math.ceil(total_tiles / tiles_per_row)
        self.sidebar_tile_scroll_max = max(0, total_rows - visible_rows)
        
        # Check for scroll button clicks
        if total_tiles > visible_rows * tiles_per_row:
            scroll_up_rect = pygame.Rect(SIDEBAR_WIDTH - 40, tiles_y - 25, 30, 20)
            scroll_down_rect = pygame.Rect(SIDEBAR_WIDTH - 40, SCREEN_HEIGHT - 140, 30, 20)
            
            if scroll_up_rect.collidepoint(pos) and self.sidebar_tile_scroll > 0:
                self.sidebar_tile_scroll -= 1
                print(f"Scrolling up: {self.sidebar_tile_scroll}")
                return
            elif scroll_down_rect.collidepoint(pos) and self.sidebar_tile_scroll < self.sidebar_tile_scroll_max:
                self.sidebar_tile_scroll += 1
                print(f"Scrolling down: {self.sidebar_tile_scroll}")
                return
        
        # Calculate visible tiles range based on scroll position
        start_index = self.sidebar_tile_scroll * tiles_per_row
        end_index = min(start_index + (visible_rows * tiles_per_row), total_tiles)
        visible_tiles = self.categories[self.selected_category][start_index:end_index]
        
        # Check for clicks on visible tiles
        for i, tile in enumerate(visible_tiles):
            row = i // tiles_per_row
            col = i % tiles_per_row
            
            tile_x = 10 + col * tile_size
            tile_y = tiles_y + row * tile_size
            
            # Skip tiles that would be below controls area
            if tile_y > SCREEN_HEIGHT - 140:
                continue
            
            tile_rect = pygame.Rect(tile_x, tile_y, tile_size, tile_size)
            
            if tile_rect.collidepoint(pos):
                # Tile was clicked - update selection
                self.selected_tile = tile
                
                # Store texture data for precise placement
                if self.selected_category in self.textures and tile in self.textures[self.selected_category]:
                    self.selected_tile_data = self.textures[self.selected_category][tile]
                else:
                    self.selected_tile_data = None
                    
                print(f"Selected tile: {tile} from category: {self.selected_category}")
                return
    
    def place_tile(self, x, y):
        """Place the selected tile at the specified map position"""
        if x < 0 or y < 0 or x >= self.map_data["width"] or y >= self.map_data["height"]:
            print(f"❌ Out of bounds: ({x}, {y})")
            return
        
        if not self.selected_tile:  # Ensure a tile is selected
            print("❌ No tile selected")
            return
        
        print(f"Placing {self.selected_tile} at ({x}, {y}) on layer {self.current_layer}")
        
        # Create coordinate key
        pos_key = f"{x},{y}"
        
        # Enhanced tile data with precise texture info
        tile_data = {
            "type": self.selected_tile,
            "x": x,
            "y": y,
            "layer": self.current_layer  # Explicitly store layer info
        }
        
        # Store critical information to ensure we can match the tile back to the texture dictionary
        if self.selected_category in self.textures and self.selected_tile in self.textures[self.selected_category]:
            try:
                texture_info = self.textures[self.selected_category][self.selected_tile]
                
                # Don't store the actual texture object as it can cause issues
                # Instead, store the metadata needed to find the texture again later
                tile_data["path"] = texture_info.get("path", "")
                tile_data["source_category"] = self.selected_category
                
                if "is_sliced" in texture_info:
                    tile_data["is_sliced"] = texture_info["is_sliced"]
                    tile_data["tileset_index"] = texture_info.get("tileset_index", 0)
                
                print(f"Stored path info for tile: {tile_data['path']}")
            except Exception as e:
                print(f"❌ Error storing tile metadata: {e}")
        else:
            print(f"⚠️ Warning: No texture found for {self.selected_tile} in {self.selected_category}")
        
        # Add tile to the current layer
        self.map_data["layers"][self.current_layer][pos_key] = tile_data
        
        # Debug info
        print(f"✅ Placed tile '{self.selected_tile}' at ({x}, {y}) on layer '{self.current_layer}'")
    
    def remove_tile(self, x, y):
        """Remove a tile at the specified map position"""
        if x < 0 or y < 0 or x >= self.map_data["width"] or y >= self.map_data["height"]:
            return
        
        # Create coordinate key
        pos_key = f"{x},{y}"
        
        # Remove tile from current layer if it exists
        if pos_key in self.map_data["layers"][self.current_layer]:
            del self.map_data["layers"][self.current_layer][pos_key]
            print(f"Removed tile at ({x}, {y}) from layer '{self.current_layer}'")
    
    def screen_to_map(self, screen_pos):
        """Convert screen coordinates to map coordinates"""
        # Make sure we're working with coordinates relative to the map area, not the whole screen
        adjusted_x = screen_pos[0] - SIDEBAR_WIDTH
        
        # Convert to tile coordinates accounting for camera position
        map_x = (adjusted_x + self.camera_x) // TILE_SIZE
        map_y = (screen_pos[1] + self.camera_y) // TILE_SIZE
        
        return map_x, map_y
    
    def map_to_screen(self, map_pos):
        """Convert map coordinates to screen coordinates"""
        screen_x = map_pos[0] * TILE_SIZE + SIDEBAR_WIDTH - self.camera_x
        screen_y = map_pos[1] * TILE_SIZE - self.camera_y
        return screen_x, screen_y
    
    def update(self):
        """Update game state"""
        pass
    
    def render(self):
        """Render the map editor interface"""
        # Clear screen
        self.screen.fill(BACKGROUND_COLOR)
        
        # Render map area
        self.render_map()
        
        # Render sidebar
        self.render_sidebar()
        
        # Update display
        pygame.display.flip()
    
    def render_map(self):
        """Render the map area"""
        # Map viewport background
        map_rect = pygame.Rect(SIDEBAR_WIDTH, 0, SCREEN_WIDTH - SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, (30, 30, 30), map_rect)
        
        # Calculate visible map area
        start_x = max(0, self.camera_x // TILE_SIZE)
        start_y = max(0, self.camera_y // TILE_SIZE)
        end_x = min(self.map_data["width"], (self.camera_x + SCREEN_WIDTH - SIDEBAR_WIDTH) // TILE_SIZE + 1)
        end_y = min(self.map_data["height"], (self.camera_y + SCREEN_HEIGHT) // TILE_SIZE + 1)
        
        # Draw the editor grid background for visual reference
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                screen_x, screen_y = self.map_to_screen((x, y))
                # Draw alternating grid pattern for visibility
                if (x + y) % 2 == 0:
                    pygame.draw.rect(self.screen, (40, 40, 40), (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                else:
                    pygame.draw.rect(self.screen, (35, 35, 35), (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
        
        # Draw base terrain layer first (always render grass or ground everywhere)
        if "terrain" in self.textures and len(self.textures["terrain"]) > 0:
            # Find a suitable ground texture
            ground_texture = None
            for tile_name in ["grass", "ground", "dirt"]:
                if tile_name in self.textures["terrain"]:
            
            for x in range(start_x, end_x):
                for y in range(start_y, end_y):
                    screen_x, screen_y = self.map_to_screen((x, y))
                    self.screen.blit(ground_texture, (screen_x, screen_y))
    
    # Render each layer
    for layer in self.map_layers:
        # Skip hidden layers
        if layer in self.hidden_layers:
            continue
        
        for pos_key, tile_data in self.map_data["layers"][layer].items():
            try:
                x, y = map(int, pos_key.split(","))
                
                # Skip tiles outside the visible area
                if x < start_x or x >= end_x or y < start_y or y >= end_y:
                                else:
                                    self.screen.blit(texture, (screen_x, screen_y))
                                texture_drawn = True
                            except Exception as e:
                                pass
                        
                        # If no texture, use color
                        if not texture_drawn:
                            color = self.tile_colors.get(tile_type, (200, 0, 200))
                            pygame.draw.rect(self.screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                        
                        # Highlight current layer
                        if layer == self.current_layer:
                            pygame.draw.rect(self.screen, (255, 255, 255, 100), 
                                            (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 1)
                except Exception as e:
                    # Skip any tiles with parsing errors
                    print(f"Error rendering tile: {e}")
                    continue
        
        # Render grid if enabled
        if self.grid_enabled:
            for x in range(start_x, end_x):
                screen_x = x * TILE_SIZE - self.camera_x + SIDEBAR_WIDTH
                pygame.draw.line(self.screen, GRID_COLOR, 
                                (screen_x, 0), 
                                (screen_x, SCREEN_HEIGHT))
            
            for y in range(start_y, end_y):
                screen_y = y * TILE_SIZE - self.camera_y
                pygame.draw.line(self.screen, GRID_COLOR, 
                                (SIDEBAR_WIDTH, screen_y), 
                                (SCREEN_WIDTH, screen_y))
    
    def render_sidebar(self):
        """Render the sidebar UI"""
        # Sidebar background
        pygame.draw.rect(self.screen, (50, 50, 50), (0, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))
        pygame.draw.line(self.screen, (100, 100, 100), (SIDEBAR_WIDTH-1, 0), (SIDEBAR_WIDTH-1, SCREEN_HEIGHT), 2)
        
        # Title
        title_text = self.font.render("Trading Legends Map Editor", True, (255, 255, 255))
        self.screen.blit(title_text, (10, 10))
        
        # Current map info
        map_info = f"Map: {self.map_data['name']} ({self.map_data['width']}x{self.map_data['height']})"
        map_text = self.small_font.render(map_info, True, (200, 200, 200))
        self.screen.blit(map_text, (10, 35))
        
        # Current layer info
        layer_text = self.small_font.render(f"Layer: {self.current_layer.upper()}", True, (200, 200, 200))
        self.screen.blit(layer_text, (10, 35 + self.small_font.get_height()))
        
        # Selected tile info with stronger visual feedback
        if self.selected_tile:
            # Draw a preview of the selected tile
            preview_rect = pygame.Rect(SIDEBAR_WIDTH - 50, 35, 40, 40)
            pygame.draw.rect(self.screen, (70, 70, 70), preview_rect)
            pygame.draw.rect(self.screen, (180, 180, 100), preview_rect, 2)  # Gold highlight
            
            # Try to draw texture if available
            texture_drawn = False
            if self.selected_category in self.textures and self.selected_tile in self.textures[self.selected_category]:
                try:
                    texture = self.textures[self.selected_category][self.selected_tile]["texture"]
                    # Scale to fit preview
                    scaled_texture = pygame.transform.scale(texture, (36, 36))
                    self.screen.blit(scaled_texture, (SIDEBAR_WIDTH - 48, 37))
                    texture_drawn = True
                except Exception as e:
                    print(f"Error drawing selected tile preview: {e}")
            
            # Fall back to color if texture not available
            if not texture_drawn:
                color = self.tile_colors.get(self.selected_tile, (200, 0, 200))
                pygame.draw.rect(self.screen, color, (SIDEBAR_WIDTH - 48, 37, 36, 36))
            
            # Draw the name
            selected_text = self.small_font.render(f"{self.selected_tile}", True, (220, 220, 100))
            self.screen.blit(selected_text, (SIDEBAR_WIDTH - 60 - selected_text.get_width(), 45))
        
        # Category selection
        category_y = 60
        
        for category in self.categories:
            bg_color = (70, 70, 70) if category == self.selected_category else (60, 60, 60)
            
            category_rect = pygame.Rect(10, category_y, SIDEBAR_WIDTH - 20, 30)
            pygame.draw.rect(self.screen, bg_color, category_rect)
            pygame.draw.rect(self.screen, (100, 100, 100), category_rect, 1)
            
            category_text = self.font.render(category.capitalize(), True, (255, 255, 255))
            self.screen.blit(category_text, (15, category_y + 5))
            
            category_y += 35
        
        # Tile display area if category is selected
        if self.selected_category:
            tiles_y = category_y + 25
            
            # Draw scroll buttons if needed
            if self.sidebar_tile_scroll_max > 0:
                # Up button - make it larger and more visible
                scroll_up_rect = pygame.Rect(SIDEBAR_WIDTH - 50, tiles_y - 25, 40, 25)
                pygame.draw.rect(self.screen, (100, 100, 120), scroll_up_rect)
                pygame.draw.rect(self.screen, (150, 150, 180), scroll_up_rect, 2)
                up_text = self.font.render("▲", True, (230, 230, 230))
                self.screen.blit(up_text, (scroll_up_rect.centerx - up_text.get_width()//2, scroll_up_rect.centery - up_text.get_height()//2))
                
                # Down button - make it larger and more visible
                scroll_down_rect = pygame.Rect(SIDEBAR_WIDTH - 50, SCREEN_HEIGHT - 140, 40, 25)
                pygame.draw.rect(self.screen, (100, 100, 120), scroll_down_rect)
                pygame.draw.rect(self.screen, (150, 150, 180), scroll_down_rect, 2)
                down_text = self.font.render("▼", True, (230, 230, 230))
                self.screen.blit(down_text, (scroll_down_rect.centerx - down_text.get_width()//2, scroll_down_rect.centery - down_text.get_height()//2))
                    
                # Show scroll position indicator
                scroll_text = self.small_font.render(f"Page {self.sidebar_tile_scroll+1}/{self.sidebar_tile_scroll_max+1}", True, (180, 180, 180))
                self.screen.blit(scroll_text, (10, tiles_y - 20))
            
            # Display tiles for current category
            if self.categories[self.selected_category]:
                tile_size = 40
                tiles_per_row = (SIDEBAR_WIDTH - 20) // tile_size
                
                # Calculate visible tiles based on scroll position
                total_tiles = len(self.categories[self.selected_category])
                tiles_per_page = (SCREEN_HEIGHT - tiles_y - 120) // tile_size * tiles_per_row
                
                start_index = self.sidebar_tile_scroll * tiles_per_row
                end_index = min(start_index + tiles_per_page, total_tiles)
                visible_tiles = self.categories[self.selected_category][start_index:end_index]
                
                for i, tile in enumerate(visible_tiles):
                    row = i // tiles_per_row
                    col = i % tiles_per_row
                    
                    tile_x = 10 + col * tile_size
                    tile_y = tiles_y + row * tile_size
                    
                    # Skip tiles that would be below controls area
                    if tile_y > SCREEN_HEIGHT - 140:
                        continue
                    
                    # Draw tile background
                    tile_rect = pygame.Rect(tile_x, tile_y, tile_size, tile_size)
                    bg_color = (90, 90, 90) if tile == self.selected_tile else (70, 70, 70)
                    pygame.draw.rect(self.screen, bg_color, tile_rect)
                    
                    # Try to draw texture if available
                    texture_drawn = False
                    
                    if self.selected_category in self.textures and tile in self.textures[self.selected_category]:
                        try:
                            texture = self.textures[self.selected_category][tile]["texture"]
                            # Scale to fit preview
                            scaled_texture = pygame.transform.scale(texture, (tile_size - 4, tile_size - 4))
                            self.screen.blit(scaled_texture, (tile_x + 2, tile_y + 2))
                            texture_drawn = True
                        except:
                            pass
                    
                    # Fall back to color if texture not available or fails
                    if not texture_drawn:
                        color = self.tile_colors.get(tile, (200, 0, 200))
                        pygame.draw.rect(self.screen, color, (tile_x + 2, tile_y + 2, tile_size - 4, tile_size - 4))
                    
                    pygame.draw.rect(self.screen, (100, 100, 100), tile_rect, 1)
                    
                    # Draw tile name on hover
                    mouse_pos = pygame.mouse.get_pos()
                    if tile_rect.collidepoint(mouse_pos):
                        # Draw tooltip with tile name
                        name_text = self.small_font.render(tile, True, (255, 255, 255))
                        
                        # Add extra info about the tile if available
                        texture_info = ""
                        if self.selected_category in self.textures and tile in self.textures[self.selected_category]:
                            if "source" in self.textures[self.selected_category][tile]:
                                source = self.textures[self.selected_category][tile]["source"]
                                if len(source) > 20:
                                    source = "..." + source[-20:]
                                texture_info = f" ({source})"
                        
                        # If we have texture info, add a second line
                        if texture_info:
                            info_text = self.small_font.render(texture_info, True, (200, 200, 200))
                            tooltip_width = max(name_text.get_width(), info_text.get_width()) + 10
                            tooltip_height = name_text.get_height() + info_text.get_height() + 10
                        else:
                            tooltip_width = name_text.get_width() + 10
                            tooltip_height = name_text.get_height() + 6
                        
                        # Position tooltip
                        tooltip_x = min(tile_x, SIDEBAR_WIDTH - tooltip_width - 5)
                        tooltip_y = tile_y - tooltip_height - 5
                        
                        # Draw tooltip background with slightly rounded corners
                        pygame.draw.rect(self.screen, (70, 70, 70), 
                                        (tooltip_x, tooltip_y, tooltip_width, tooltip_height))
                        pygame.draw.rect(self.screen, (120, 120, 120), 
                                        (tooltip_x, tooltip_y, tooltip_width, tooltip_height), 1)
                        
                        # Draw tooltip text
                        self.screen.blit(name_text, (tooltip_x + 5, tooltip_y + 3))
                        if texture_info:
                            self.screen.blit(info_text, (tooltip_x + 5, tooltip_y + name_text.get_height() + 5))
        
        # Controls info at bottom
        controls_y = SCREEN_HEIGHT - 120
        controls = [
            "Controls:",
            "Arrow keys/WASD: Pan camera",
            "G: Toggle grid",
            "1-5: Switch layers",
            "Ctrl+S: Save map",
            "Ctrl+L: Load map",
            "Left click: Place tile",
            "Right click: Remove tile"
        ]
        
        for i, control in enumerate(controls):
            control_text = self.small_font.render(control, True, (200, 200, 200))
            self.screen.blit(control_text, (10, controls_y + i * 15))
    
    def save_map(self):
        """Save the current map to a JSON file"""
        # Ensure maps directory exists
        maps_dir = os.path.join(os.getcwd(), "maps")
        os.makedirs(maps_dir, exist_ok=True)
        
        # Generate filename from map name
        filename = os.path.join(maps_dir, f"{self.map_data['name'].replace(' ', '_').lower()}.json")
        
        # Save map data
        with open(filename, 'w') as f:
            json.dump(self.map_data, f, indent=2)
            
        print(f"✅ Map saved to {filename}")
    
    def load_map(self):
        """Load a map from a JSON file"""
        # Ensure maps directory exists
        maps_dir = os.path.join(os.getcwd(), "maps")
        
        if not os.path.exists(maps_dir):
            print("❌ No maps directory found")
            return
        
        # List available maps
        map_files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
        
        if not map_files:
            print("❌ No map files found in maps directory")
            return
        
        print("\nAvailable maps:")
        for i, map_file in enumerate(map_files):
            print(f"  {i+1}. {map_file}")
        
        # For now, just load the first map
        if map_files:
            try:
                map_path = os.path.join(maps_dir, map_files[0])
                with open(map_path, 'r') as f:
                    self.map_data = json.load(f)
                print(f"✅ Loaded map from {map_path}")
            except Exception as e:
                print(f"❌ Error loading map: {e}")


if __name__ == "__main__":
    editor = StandaloneMapEditor()
    editor.run()
