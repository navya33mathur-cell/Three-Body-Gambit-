"""
Centralized UI Manager for Modal Dialog handling in Orbital Echo.
Routes input events cleanly to active modals and ensures input focus never traps the user.
"""

import pygame
from typing import List, Optional

class UIModal:
    """Base class for UI Modal windows."""
    def __init__(self, title: str, width: int = 600, height: int = 400):
        self.title = title
        self.width = width
        self.height = height
        self.is_open = True

    def close(self):
        self.is_open = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Override in subclass. Return True if event was consumed."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        return False

    def update(self, dt: float):
        pass

    def render(self, screen: pygame.Surface):
        """Override in subclass."""
        pass


class UIManager:
    """Manages active stack of UI Modals."""
    def __init__(self):
        self.modals: List[UIModal] = []

    def open_modal(self, modal: UIModal):
        """Pushes a modal onto the top of the modal stack."""
        self.modals.append(modal)

    def close_top_modal(self):
        """Closes the current top-most modal."""
        if self.modals:
            self.modals.pop()

    def has_active_modal(self) -> bool:
        """Returns True if any modal window is currently open."""
        return len(self.modals) > 0

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Routes event to top modal first. Returns True if event was consumed.
        """
        if not self.modals:
            return False

        top_modal = self.modals[-1]
        consumed = top_modal.handle_event(event)

        # Check if modal closed itself during event handling
        if not top_modal.is_open:
            self.modals.remove(top_modal)

        return consumed

    def update(self, dt: float):
        """Updates top modal."""
        if self.modals:
            self.modals[-1].update(dt)

    def render(self, screen: pygame.Surface):
        """Renders active modals in stack order."""
        for modal in self.modals:
            modal.render(screen)
