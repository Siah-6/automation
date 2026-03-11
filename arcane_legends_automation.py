import cv2
import numpy as np
import mss
import pyautogui
import time
import threading
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

class GameState(Enum):
    # Hub states
    IN_HUB = "in_hub"
    MOVING_TO_PORTAL = "moving_to_portal"
    PORTAL_MENU_OPEN = "portal_menu_open"
    ENERGY_CONFIRMATION = "energy_confirmation"
    LOW_ENERGY_REFILL = "low_energy_refill"
    
    # Dungeon states
    IN_DUNGEON = "in_dungeon"
    COMBAT = "combat"
    LOOTING = "looting"
    MOVING_TO_EXIT = "moving_to_exit"
    OUTSIDE_DUNGEON = "outside_dungeon"

@dataclass
class DetectedObject:
    position: Tuple[int, int]
    confidence: float
    object_type: str

class ScreenCapture:
    def __init__(self, monitor_index: int = 1):
        self.sct = mss.mss()
        self.monitors = self.sct.monitors
        self.monitor = self.monitors[monitor_index] if monitor_index < len(self.monitors) else self.monitors[1]
        print(f"Using monitor {monitor_index}: {self.monitor}")
        
    def capture_region(self, region: Tuple[int, int, int, int] = None) -> np.ndarray:
        """Capture screen region (x, y, width, height)"""
        if region:
            # For fullscreen, regions are relative to full monitor
            x, y, w, h = region
            monitor = {"top": y + 0, "left": x + 0, "width": w, "height": h}
            print(f"Capturing region: x={x}, y={y}, w={w}, h={h}")
        else:
            # Fullscreen game - use entire monitor
            monitor = {
                "top": 0,
                "left": 0,
                "width": 1920,
                "height": 1080
            }
            print("Capturing fullscreen game window")

        img = self.sct.grab(monitor)
        return np.array(img)
class VisualDetector:
    def __init__(self):
        self.enemy_templates = []
        self.loot_templates = []
        self.portal_templates = []
        
        # Detection regions for fullscreen mode (game content starts at 168, 41)
        self.hp_bar_region = (168+40, 41+40, 340, 110)  # (208, 81, 340, 110)
        self.energy_bar_region = (750, 40, 400, 100)  # Back to working region
        self.skill_bar_region = (168+1220, 41+520, 350, 340)  # (1388, 561, 350, 340)
        self.hotbar_region = (168+1120, 41+240, 300, 200)  # (1288, 281, 300, 200)
        self.combat_area_region = (168+260, 41+140, 820, 540)  # (428, 181, 820, 540)
        self.portal_menu_region = (168+520, 41+150, 560, 520)  # (688, 191, 560, 520)
        self.interaction_button_region = (1500, 850, 250, 180)  # Correct position for interaction button
        
    def load_templates(self):
        """Load template images for detection - user needs to provide these"""
        # This would load template images for enemies, loot, portals
        # For now, we'll use color-based detection
        pass
        
    def detect_enemies(self, frame: np.ndarray) -> List[DetectedObject]:
        """Detect enemies using color and shape analysis"""
        enemies = []
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Example: Detect red/orange enemies (adjust HSV values based on game)
        lower_enemy = np.array([0, 120, 70])
        upper_enemy = np.array([20, 255, 255])
        mask = cv2.inRange(hsv, lower_enemy, upper_enemy)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Filter small noise
                x, y, w, h = cv2.boundingRect(contour)
                center = (x + w // 2, y + h // 2)
                confidence = min(area / 1000, 1.0)  # Simple confidence based on size
                enemies.append(DetectedObject(center, confidence, "enemy"))
                
        return enemies
    
    def detect_loot(self, frame: np.ndarray) -> List[DetectedObject]:
        """Detect loot items using color detection"""
        loot_items = []
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Example: Detect yellow/gold loot
        lower_loot = np.array([20, 100, 100])
        upper_loot = np.array([30, 255, 255])
        mask = cv2.inRange(hsv, lower_loot, upper_loot)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 50:
                x, y, w, h = cv2.boundingRect(contour)
                center = (x + w // 2, y + h // 2)
                confidence = min(area / 500, 1.0)
                loot_items.append(DetectedObject(center, confidence, "loot"))
                
        return loot_items
    
    def detect_portal(self, frame: np.ndarray) -> Optional[DetectedObject]:
        """Detect exit portal"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Example: Detect blue/purple portal
        lower_portal = np.array([100, 50, 50])
        upper_portal = np.array([150, 255, 255])
        mask = cv2.inRange(hsv, lower_portal, upper_portal)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Find largest contour (likely the portal)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            if area > 200:
                x, y, w, h = cv2.boundingRect(largest_contour)
                center = (x + w // 2, y + h // 2)
                confidence = min(area / 1000, 1.0)
                return DetectedObject(center, confidence, "portal")
                
        return None
    
    def check_hp_bar(self, frame: np.ndarray) -> float:
        """Check HP level (returns percentage 0-1)"""
        # Extract HP bar region
        hp_region = frame[self.hp_bar_region[1]:self.hp_bar_region[1]+self.hp_bar_region[3],
                          self.hp_bar_region[0]:self.hp_bar_region[0]+self.hp_bar_region[2]]
        
        # Convert to HSV and detect red HP bar
        hsv = cv2.cvtColor(hp_region, cv2.COLOR_BGR2HSV)
        lower_hp = np.array([0, 120, 70])
        upper_hp = np.array([10, 255, 255])
        mask = cv2.inRange(hsv, lower_hp, upper_hp)
        
        # Calculate HP percentage
        hp_pixels = cv2.countNonZero(mask)
        total_pixels = hp_region.shape[0] * hp_region.shape[1]
        hp_percentage = hp_pixels / total_pixels if total_pixels > 0 else 0
        
        return min(hp_percentage * 2, 1.0)  # Normalize to 0-1
    
    def check_skill_cooldowns(self, frame: np.ndarray) -> List[bool]:
        """Check which skills are available (no cooldown)"""
        skills_ready = []
        
        # Extract skill bar region
        skill_region = frame[self.skill_bar_region[1]:self.skill_bar_region[1]+self.skill_bar_region[3],
                            self.skill_bar_region[0]:self.skill_bar_region[0]+self.skill_bar_region[2]]
        
        # Simple approach: check brightness of skill slots (dark = cooldown)
        gray = cv2.cvtColor(skill_region, cv2.COLOR_BGR2GRAY)
        
        # Divide skill bar into 4 skill slots (adjust based on game)
        slot_width = skill_region.shape[1] // 4
        for i in range(4):
            slot = gray[:, i*slot_width:(i+1)*slot_width]
            brightness = np.mean(slot)
            skills_ready.append(brightness > 100)  # Threshold for "ready" skills
            
        return skills_ready
    
    def detect_energy_icons(self, frame: np.ndarray) -> int:
        """Count available energy icons from top UI"""
        x, y, w, h = self.energy_bar_region
        energy_region = frame[y:y+h, x:x+w]
        
        hsv = cv2.cvtColor(energy_region, cv2.COLOR_BGR2HSV)
        
        # More inclusive HSV range for energy leaf icons
        lower_energy = np.array([40, 80, 80])
        upper_energy = np.array([85, 255, 255])
        mask = cv2.inRange(hsv, lower_energy, upper_energy)
        
        
        # Find contours and count energy icons
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by position and size to isolate energy icons
        energy_count = 0
        detected_positions = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 30 <= area <= 800:  # More inclusive size range for energy icons
                # Check if contour is roughly circular/leaf-shaped
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                if 0.6 <= aspect_ratio <= 1.4:  # More strict for leaf shapes
                    # Energy icons are typically in a horizontal line at similar Y position
                    # and have specific spacing between them
                    detected_positions.append((x, y, w, h, area))
        
        # Sort by X position (left to right)
        detected_positions.sort(key=lambda pos: pos[0])
        
        # Filter for energy icon pattern: 3 icons in horizontal line with similar Y
        if len(detected_positions) >= 2:
            # Find the most common Y position (energy icons align horizontally)
            y_positions = [pos[1] for pos in detected_positions]
            most_common_y = max(set(y_positions), key=y_positions.count)
            
            # Count icons near this Y position (within 20 pixels)
            for x, y, w, h, area in detected_positions:
                if abs(y - most_common_y) <= 20:
                    energy_count += 1
                    # Draw bounding box for debugging
                    cv2.rectangle(energy_region, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(energy_region, f"Icon {energy_count}", (x, y-5), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Energy should be 0-3, so cap it
        energy_count = min(energy_count, 3)
        
        print(f"Energy detection: found {energy_count} icons, region: {self.energy_bar_region}")
        return energy_count
    
    def detect_green_portal(self, frame: np.ndarray) -> Optional[DetectedObject]:
    # Crop to gameplay area only
        x, y, w, h = self.combat_area_region
        region = frame[y:y+h, x:x+w]

        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)

        lower_portal = np.array([40, 150, 150])
        upper_portal = np.array([80, 255, 255])
        mask = cv2.inRange(hsv, lower_portal, upper_portal)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best = None
        best_score = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1200:
                continue

            x2, y2, w2, h2 = cv2.boundingRect(contour)
            aspect_ratio = w2 / float(h2)

            # Portal should be a fairly tall glowing object, not a tiny green blob
            if not (0.5 <= aspect_ratio <= 1.8):
                continue

            score = area
            if score > best_score:
                best_score = score
                best = (x2, y2, w2, h2, area)

        if best is not None:
            x2, y2, w2, h2, area = best
            cx = x + x2 + w2 // 2  # Add region offset to get full screen coordinates
            cy = y + y2 + h2 // 2
            center = (cx, cy)
            confidence = min(area / 4000, 1.0)
            return DetectedObject(center, confidence, "green_portal")

        return None
    
    def detect_interaction_button(self, frame: np.ndarray) -> bool:
        """Detect if attack button changed to interaction button"""
        button_region = frame[self.interaction_button_region[1]:self.interaction_button_region[1]+self.interaction_button_region[3],
                              self.interaction_button_region[0]:self.interaction_button_region[0]+self.interaction_button_region[2]]
        
        hsv = cv2.cvtColor(button_region, cv2.COLOR_BGR2HSV)
        
        # Detect interaction button (usually yellow/orange glow when near portal)
        lower_interact = np.array([15, 100, 150])
        upper_interact = np.array([60, 255, 255])
        mask = cv2.inRange(hsv, lower_interact, upper_interact)
      
        
        # Check if there's significant interaction color
        interact_pixels = cv2.countNonZero(mask)
        total_pixels = button_region.shape[0] * button_region.shape[1]
        interact_ratio = interact_pixels / total_pixels if total_pixels > 0 else 0
        
        print(f"Interaction detection: ratio={interact_ratio:.3f}, region={self.interaction_button_region}")
        return interact_ratio > 0.1  # Lower threshold for better detection
    
    def detect_portal_menu_options(self, frame: np.ndarray) -> List[str]:
        """Detect available options in portal menu"""
        menu_region = frame[self.portal_menu_region[1]:self.portal_menu_region[1]+self.portal_menu_region[3],
                            self.portal_menu_region[0]:self.portal_menu_region[0]+self.portal_menu_region[2]]
        
        # Convert to grayscale for text detection
        gray = cv2.cvtColor(menu_region, cv2.COLOR_BGR2GRAY)
        
        options = []
        
        # Simple color-based detection for menu buttons
        hsv = cv2.cvtColor(menu_region, cv2.COLOR_BGR2HSV)
        
        # Detect button backgrounds (usually blue/purple)
        lower_button = np.array([100, 50, 50])
        upper_button = np.array([150, 255, 255])
        mask = cv2.inRange(hsv, lower_button, upper_button)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Count button-like contours
        button_count = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # Menu buttons should be substantial
                button_count += 1
        
        # Based on button count, infer available options
        if button_count >= 3:
            options.extend(["Go Normal", "Go Elite", "Leave"])
        elif button_count >= 2:
            options.extend(["Go Normal", "Leave"])
        elif button_count >= 1:
            options.append("Leave")
            
        return options
    
    def detect_energy_confirmation(self, frame: np.ndarray) -> bool:
        """Detect energy confirmation screen"""
        # Look for confirmation dialog in center area
        confirm_region = frame[self.portal_menu_region[1]:self.portal_menu_region[1]+self.portal_menu_region[3],
                               self.portal_menu_region[0]:self.portal_menu_region[0]+self.portal_menu_region[2]]
        
        # Check for typical confirmation dialog colors (blue/purple background)
        hsv = cv2.cvtColor(confirm_region, cv2.COLOR_BGR2HSV)
        lower_confirm = np.array([100, 50, 50])
        upper_confirm = np.array([150, 255, 255])
        mask = cv2.inRange(hsv, lower_confirm, upper_confirm)
        
        confirm_pixels = cv2.countNonZero(mask)
        total_pixels = confirm_region.shape[0] * confirm_region.shape[1]
        confirm_ratio = confirm_pixels / total_pixels if total_pixels > 0 else 0
        
        return confirm_ratio > 0.5  # High ratio indicates confirmation screen
    
    def detect_hotbar_energy_kit(self, frame: np.ndarray) -> Optional[DetectedObject]:
        """Detect energy refill kit in hotbar"""
        hotbar_region = frame[self.hotbar_region[1]:self.hotbar_region[1]+self.hotbar_region[3],
                              self.hotbar_region[0]:self.hotbar_region[0]+self.hotbar_region[2]]
        
        hsv = cv2.cvtColor(hotbar_region, cv2.COLOR_BGR2HSV)
        
        # Detect energy kit (usually distinctive color like yellow/orange)
        lower_kit = np.array([15, 100, 100])
        upper_kit = np.array([35, 255, 255])
        mask = cv2.inRange(hsv, lower_kit, upper_kit)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Hotbar items should be visible
                x, y, w, h = cv2.boundingRect(contour)
                center = (self.hotbar_region[0] + x + w // 2, self.hotbar_region[1] + y + h // 2)
                confidence = min(area / 500, 1.0)
                return DetectedObject(center, confidence, "energy_kit")
                
        return None

class InputController:
    def __init__(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05
        self.current_keys = set()

    def move_towards(self, target: Tuple[int, int], screen_center: Tuple[int, int]):
        """Move character towards target position with proper key hold/release"""
        dx = target[0] - screen_center[0]
        dy = target[1] - screen_center[1]

        keys_to_hold = set()

        # Horizontal
        if dx > 60:
            keys_to_hold.add('d')
        elif dx < -60:
            keys_to_hold.add('a')

        # Vertical
        if dy > 60:
            keys_to_hold.add('s')
        elif dy < -60:
            keys_to_hold.add('w')

        # Release keys no longer needed
        for key in self.current_keys - keys_to_hold:
            pyautogui.keyUp(key)

        # Press new keys
        for key in keys_to_hold - self.current_keys:
            pyautogui.keyDown(key)

        self.current_keys = keys_to_hold

    def stop_movement(self):
        """Stop all movement"""
        for key in list(self.current_keys):
            pyautogui.keyUp(key)
        self.current_keys.clear()

    def use_skill(self, skill_index: int):
        skill_keys = ['1', '2', '3', '4']
        if 0 <= skill_index < len(skill_keys):
            pyautogui.press(skill_keys[skill_index])

    def pick_up_loot(self):
        pyautogui.press('space')

    def interact_with_portal(self):
        self.stop_movement()
        time.sleep(0.1)
        pyautogui.press('e')

    def click_position(self, position: Tuple[int, int]):
        pyautogui.click(position[0], position[1])
        time.sleep(0.2)

    def use_energy_kit(self):
        pyautogui.press('r')

    def select_menu_option(self, option_index: int):
        pyautogui.press(str(option_index))
        time.sleep(0.3)

    def confirm_action(self):
        pyautogui.press('enter')
        time.sleep(0.3)

class DecisionEngine:
    def __init__(self, detector: VisualDetector, controller: InputController):
        self.detector = detector
        self.controller = controller
        self.current_state = GameState.IN_HUB
        self.last_portal = None
        self.last_portal_time = 0
        self.portal_memory_time = 1.0  # seconds
        self.last_combat_time = 0
        self.combat_timeout = 3.0  # Seconds to wait after combat before moving to exit
        self.energy_threshold = 1  # Minimum energy to enter dungeon
        self.last_menu_action_time = 0
        self.menu_action_delay = 1.0  # Delay between menu actions
        
    def update(self, frame: np.ndarray, screen_center: Tuple[int, int]):
        enemies = self.detector.detect_enemies(frame)
        loot = self.detector.detect_loot(frame)
        portal = self.detector.detect_portal(frame)
        green_portal = self.detector.detect_green_portal(frame)

        print("STATE:", self.current_state)
        print("green_portal:", green_portal.position if green_portal else None)

        # Portal memory system
        if green_portal:
            self.last_portal = green_portal
            self.last_portal_time = time.time()
        else:
            if time.time() - self.last_portal_time < self.portal_memory_time:
                green_portal = self.last_portal
        print("green_portal:", green_portal.position if green_portal else None)
        hp_level = self.detector.check_hp_bar(frame)
        skills_ready = self.detector.check_skill_cooldowns(frame)
        energy_count = self.detector.detect_energy_icons(frame)
        interaction_button = self.detector.detect_interaction_button(frame)
        menu_options = self.detector.detect_portal_menu_options(frame)
        energy_confirmation = self.detector.detect_energy_confirmation(frame)
        energy_kit = self.detector.detect_hotbar_energy_kit(frame)
        
        # State machine
        if self.current_state == GameState.IN_HUB:
            # Stop movement when in hub (not moving to portal)
            self.controller.stop_movement()
            # Check energy first
            if energy_count < self.energy_threshold:
                self.current_state = GameState.LOW_ENERGY_REFILL
                self.handle_energy_refill(energy_kit)
            elif green_portal:
                self.current_state = GameState.MOVING_TO_PORTAL
                self.handle_move_to_portal(green_portal, screen_center, interaction_button)
            else:
                # Explore hub to find portal
                self.controller.move_towards((screen_center[0] + 100, screen_center[1]), screen_center)
                
        elif self.current_state == GameState.MOVING_TO_PORTAL:
            if green_portal:
                self.handle_move_to_portal(green_portal, screen_center, interaction_button)
            elif interaction_button:
                self.current_state = GameState.PORTAL_MENU_OPEN
                self.handle_portal_menu(menu_options)
            else:
                # Portal lost, search again
                self.current_state = GameState.IN_HUB
                
        elif self.current_state == GameState.PORTAL_MENU_OPEN:
            # Stop movement when in menu
            self.controller.stop_movement()
            if energy_confirmation:
                self.current_state = GameState.ENERGY_CONFIRMATION
                self.handle_energy_confirmation()
            elif menu_options:
                self.handle_portal_menu(menu_options)
            else:
                # Menu closed, return to hub
                self.current_state = GameState.IN_HUB
                
        elif self.current_state == GameState.ENERGY_CONFIRMATION:
            if energy_confirmation:
                self.handle_energy_confirmation()
            else:
                # Confirmation done, should be in dungeon
                self.current_state = GameState.IN_DUNGEON
                
        elif self.current_state == GameState.LOW_ENERGY_REFILL:
            # Stop movement when refilling energy
            self.controller.stop_movement()
            if energy_count >= self.energy_threshold:
                self.current_state = GameState.IN_HUB
            elif energy_kit:
                self.handle_energy_refill(energy_kit)
            else:
                # No energy kit available, wait
                time.sleep(2)
                
        elif self.current_state == GameState.IN_DUNGEON:
            if enemies:
                self.current_state = GameState.COMBAT
                self.handle_combat(enemies, skills_ready, screen_center)
            elif loot:
                self.current_state = GameState.LOOTING
                self.handle_looting(loot, screen_center)
            elif portal:
                self.current_state = GameState.MOVING_TO_EXIT
                self.handle_move_to_exit(portal, screen_center)
            else:
                # Move forward to explore dungeon
                self.controller.move_towards((screen_center[0], screen_center[1] - 100), screen_center)
                
        elif self.current_state == GameState.COMBAT:
            if enemies:
                self.handle_combat(enemies, skills_ready, screen_center)
                self.last_combat_time = time.time()
            else:
                if time.time() - self.last_combat_time > self.combat_timeout:
                    self.current_state = GameState.IN_DUNGEON
                elif loot:
                    self.current_state = GameState.LOOTING
                    self.handle_looting(loot, screen_center)
                    
        elif self.current_state == GameState.LOOTING:
            if loot:
                self.handle_looting(loot, screen_center)
            else:
                self.current_state = GameState.IN_DUNGEON
                
        elif self.current_state == GameState.MOVING_TO_EXIT:
            if portal:
                self.handle_move_to_exit(portal, screen_center)
            else:
                # Portal used, should be back in hub
                self.current_state = GameState.IN_HUB
        
        # Health check
        if hp_level < 0.3:  # Low health
            self.controller.stop_movement()
            # Use healing potion if available
            pyautogui.press('q')  # Common healing key
    
    def handle_combat(self, enemies: List[DetectedObject], skills_ready: List[bool], screen_center: Tuple[int, int]):
        """Handle combat logic"""
        if not enemies:
            return
            
        # Find closest enemy
        closest_enemy = min(enemies, key=lambda e: np.sqrt((e.position[0] - screen_center[0])**2 + 
                                                         (e.position[1] - screen_center[1])**2))
        
        # Move towards enemy
        self.controller.move_towards(closest_enemy.position, screen_center)
        
        # Use available skills
        for i, ready in enumerate(skills_ready):
            if ready:
                self.controller.use_skill(i)
                break  # Use one skill at a time
    
    def handle_looting(self, loot: List[DetectedObject], screen_center: Tuple[int, int]):
        """Handle loot collection"""
        if not loot:
            return
            
        # Move towards closest loot
        closest_loot = min(loot, key=lambda l: np.sqrt((l.position[0] - screen_center[0])**2 + 
                                                       (l.position[1] - screen_center[1])**2))
        
        distance = np.sqrt((closest_loot.position[0] - screen_center[0])**2 + 
                          (closest_loot.position[1] - screen_center[1])**2)
        
        if distance < 50:  # Close enough to pick up
            self.controller.pick_up_loot()
        else:
            self.controller.move_towards(closest_loot.position, screen_center)
    
    def handle_move_to_portal(self, portal: DetectedObject, screen_center: Tuple[int, int], interaction_button: bool):
        """Handle moving to and interacting with hub portal"""
        distance = np.sqrt((portal.position[0] - screen_center[0])**2 + 
                          (portal.position[1] - screen_center[1])**2)
        
        if distance < 50:  # Close enough to interact
            if interaction_button:
                self.controller.interact_with_portal()
            else:
                # Try to interact anyway
                self.controller.interact_with_portal()
        else:
            self.controller.move_towards(portal.position, screen_center)
    
    def handle_portal_menu(self, menu_options: List[str]):
        """Handle portal menu selection"""
        current_time = time.time()
        if current_time - self.last_menu_action_time < self.menu_action_delay:
            return
            
        if "Go Normal" in menu_options:
            # Select "Go Normal" (usually option 1)
            self.controller.select_menu_option(1)
            self.last_menu_action_time = current_time
        elif "Leave" in menu_options:
            # Only leave option available, close menu
            self.controller.select_menu_option(1)
            self.last_menu_action_time = current_time
    
    def handle_energy_confirmation(self):
        """Handle energy confirmation dialog"""
        current_time = time.time()
        if current_time - self.last_menu_action_time < self.menu_action_delay:
            return
            
        # Confirm energy usage
        self.controller.confirm_action()
        self.last_menu_action_time = current_time
    
    def handle_energy_refill(self, energy_kit: Optional[DetectedObject]):
        """Handle energy refill using hotbar kit"""
        if energy_kit:
            # Click on energy kit in hotbar
            self.controller.click_position(energy_kit.position)
        else:
            # Try to use energy kit by keybind
            self.controller.use_energy_kit()
    
    def handle_move_to_exit(self, portal: DetectedObject, screen_center: Tuple[int, int]):
        """Handle moving to and using dungeon exit portal"""
        distance = np.sqrt((portal.position[0] - screen_center[0])**2 + 
                          (portal.position[1] - screen_center[1])**2)
        
        if distance < 50:  # Close enough to interact
            self.controller.interact_with_portal()
        else:
            self.controller.move_towards(portal.position, screen_center)

class ArcaneLegendsAutomation:
    def __init__(self):
        self.screen_capture = ScreenCapture()
        self.detector = VisualDetector()
        self.controller = InputController()
        self.decision_engine = DecisionEngine(self.detector, self.controller)
        self.running = False
        self.fps = 15  # Target FPS for detection loop
        self.frame_time = 1.0 / self.fps
        
    def start(self):
        """Start the automation"""
        self.running = True
        print("Starting Arcane Legends Automation...")
        print("Press Ctrl+C to stop")
        
        try:
            self.main_loop()
        except KeyboardInterrupt:
            print("\nStopping automation...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the automation"""
        self.running = False
        self.controller.stop_movement()
        print("Automation stopped")
    
    def main_loop(self):
        """Main automation loop"""

        screen_width = self.screen_capture.monitor["width"]
        screen_height = self.screen_capture.monitor["height"]
        screen_center = (screen_width // 2, screen_height // 2)

        print("Capturing in 3 seconds... switch to the game window")
        time.sleep(3)

        while self.running:

            start_time = time.time()

            # Capture screen
            frame = self.screen_capture.capture_region()

            # Run automation logic
            self.decision_engine.update(frame, screen_center)

            # Maintain FPS
            elapsed = time.time() - start_time
            if elapsed < self.frame_time:
                time.sleep(self.frame_time - elapsed)
            
if __name__ == "__main__":
    automation = ArcaneLegendsAutomation()
    automation.start()
