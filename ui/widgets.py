"""
UI Widget Primitives for Orbital Echo.
Includes Button, Label, NumberInput, Dropdown, and Panel.
"""

import pygame
from typing import Tuple, List, Callable, Optional

class UIButton:
    """Interactive clickable UI Button."""
    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        text: str,
        callback: Optional[Callable] = None,
        bg_color: Tuple[int, int, int] = (40, 60, 90),
        hover_color: Tuple[int, int, int] = (60, 90, 140),
        text_color: Tuple[int, int, int] = (240, 245, 255)
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

    def render(self, screen: pygame.Surface, font: pygame.font.Font):
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        pygame.draw.rect(screen, (90, 130, 190), self.rect, width=1, border_radius=6)

        txt_surf = font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)


class UINumberInput:
    """Interactive numeric text field input."""
    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        value: float,
        callback: Optional[Callable[[float], None]] = None
    ):
        self.rect = pygame.Rect(rect)
        self.value = float(value)
        self.text = str(value)
        self.callback = callback
        self.is_focused = False

    def set_value(self, val: float):
        self.value = float(val)
        self.text = str(val)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_focused = self.rect.collidepoint(event.pos)
            return self.is_focused
        elif event.type == pygame.KEYDOWN and self.is_focused:
            if event.key == pygame.K_RETURN:
                self.confirm()
                self.is_focused = False
                return True
            elif event.key == pygame.K_ESCAPE:
                self.text = str(self.value)
                self.is_focused = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            else:
                if event.unicode and (event.unicode.isdigit() or event.unicode in ['.', '-', 'e', 'E']):
                    self.text += event.unicode
                    return True
        return False

    def confirm(self):
        try:
            self.value = float(self.text)
            if self.callback:
                self.callback(self.value)
        except ValueError:
            self.text = str(self.value)

    def render(self, screen: pygame.Surface, font: pygame.font.Font):
        bg = (25, 35, 50) if self.is_focused else (15, 20, 30)
        border = (120, 180, 255) if self.is_focused else (50, 70, 100)
        pygame.draw.rect(screen, bg, self.rect, border_radius=4)
        pygame.draw.rect(screen, border, self.rect, width=1, border_radius=4)

        txt_surf = font.render(self.text, True, (240, 240, 255))
        screen.blit(txt_surf, (self.rect.x + 8, self.rect.y + 4))


class UIDropdown:
    """Interactive selectable Dropdown UI element."""
    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        options: List[str],
        selected_index: int = 0,
        callback: Optional[Callable[[int, str], None]] = None
    ):
        self.rect = pygame.Rect(rect)
        self.options = options
        self.selected_index = selected_index
        self.callback = callback
        self.is_open = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return True
            elif self.is_open:
                # Check option click
                for i in range(len(self.options)):
                    opt_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                    if opt_rect.collidepoint(event.pos):
                        self.selected_index = i
                        self.is_open = False
                        if self.callback:
                            self.callback(i, self.options[i])
                        return True
                self.is_open = False
        return False

    def render(self, screen: pygame.Surface, font: pygame.font.Font):
        # Header box
        pygame.draw.rect(screen, (25, 35, 50), self.rect, border_radius=4)
        pygame.draw.rect(screen, (70, 100, 140), self.rect, width=1, border_radius=4)

        sel_str = self.options[self.selected_index] if 0 <= self.selected_index < len(self.options) else ""
        txt_surf = font.render(sel_str + " v", True, (230, 240, 255))
        screen.blit(txt_surf, (self.rect.x + 8, self.rect.y + 4))

        # Expanded list
        if self.is_open:
            for i, opt in enumerate(self.options):
                opt_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                bg = (40, 60, 90) if i == self.selected_index else (20, 28, 40)
                pygame.draw.rect(screen, bg, opt_rect)
                pygame.draw.rect(screen, (60, 85, 120), opt_rect, width=1)

                opt_surf = font.render(opt, True, (240, 245, 255))
                screen.blit(opt_surf, (opt_rect.x + 8, opt_rect.y + 4))
