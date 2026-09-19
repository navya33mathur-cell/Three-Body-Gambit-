"""Keyboard and mouse input for the scientific interface."""

import pygame


class InputController:
    def __init__(self, app):
        self.app = app

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.app.is_running = False
                return

            if self.app.ui_manager.has_active_modal():
                if self.app.ui_manager.handle_event(event):
                    continue
            else:
                if self.app.scientific_renderer.handle_event(event, self.app.dual_system):
                    continue

            if event.type == pygame.VIDEORESIZE:
                self.app.on_resize(event.w, event.h)
                continue

            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)

    def handle_keydown(self, key: int):
        if key == pygame.K_SPACE:
            self.app.is_paused = not self.app.is_paused
        elif key == pygame.K_r:
            self.app.reset_experiment()
        elif key == pygame.K_s:
            self.app.step_single_frame()
        elif key == pygame.K_f:
            self.app.auto_frame_camera()
        elif key == pygame.K_t:
            self.app.show_trails = not self.app.show_trails
        elif key == pygame.K_v:
            self.app.show_vectors = not self.app.show_vectors
        elif key == pygame.K_l:
            self.app.show_labels = not self.app.show_labels
        elif pygame.K_1 <= key <= pygame.K_5:
            self.app.load_preset(key - pygame.K_1)
        elif key == pygame.K_LEFTBRACKET:
            self.app.adjust_dt(0.5)
        elif key == pygame.K_RIGHTBRACKET:
            self.app.adjust_dt(2.0)
        elif key == pygame.K_h:
            self.app.toggle_help()
        elif key == pygame.K_TAB:
            self.app.open_controls_modal()
        elif key == pygame.K_e:
            self.app.open_editor_modal()
        elif key == pygame.K_m:
            self.app.open_measurements_modal()
        elif key == pygame.K_a:
            self.app.open_audit_modal()
        elif key == pygame.K_F5:
            self.app.save_experiment_json()
        elif key == pygame.K_F9:
            self.app.load_experiment_json()
        elif key == pygame.K_ESCAPE:
            if self.app.scientific_renderer.help_open:
                self.app.toggle_help()
            elif self.app.ui_manager.has_active_modal():
                self.app.ui_manager.close_top_modal()
