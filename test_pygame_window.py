#!/usr/bin/env python3
import pygame

pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Pygame Test Window")

# Set SDL video driver for Mac
import os
os.environ['SDL_VIDEODRIVER'] = 'cocoa'  # Mac-specific driver

running = True
while running:
    screen.fill((50, 50, 90))  # Dark blue background
    pygame.display.flip()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

pygame.quit()
print("Pygame test completed successfully!")
