"""
Calibration tool for Arcane Legends Automation
Use this tool to find the correct HSV color values and screen regions
"""

import cv2
import numpy as np
import mss
import pyautogui
import time
from dataclasses import dataclass

@dataclass
class CalibrationData:
    hsv_values: dict
    regions: dict

class ColorCalibrator:
    def __init__(self):
        self.sct = mss.mss()
        self.monitors = self.sct.monitors
        self.monitor = self.monitors[1]  # Default to secondary monitor
        self.calibration_data = CalibrationData({}, {})
        self.current_frame = None
        self.selected_region = None
        self.drawing = False
        self.start_point = None
        
    def capture_screen(self):
        """Capture the full screen"""
        img = self.sct.grab(self.monitor)
        frame = np.array(img)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    
    def select_region(self, event, x, y, flags, param):
        """Mouse callback for region selection"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_point = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            if self.current_frame is not None:
                temp_frame = self.current_frame.copy()
                cv2.rectangle(temp_frame, self.start_point, (x, y), (0, 255, 0), 2)
                cv2.imshow('Screen Capture', temp_frame)
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            if self.start_point:
                self.selected_region = (self.start_point[0], self.start_point[1], 
                                       x - self.start_point[0], y - self.start_point[1])
                print(f"Selected region: {self.selected_region}")
    
    def get_hsv_at_point(self, frame, x, y):
        """Get HSV values at a specific point"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        return tuple(hsv[y, x])
    
    def sample_colors_in_region(self, frame, region):
        """Sample colors within a selected region"""
        x, y, w, h = region
        region_frame = frame[y:y+h, x:x+w]
        hsv = cv2.cvtColor(region_frame, cv2.COLOR_BGR2HSV)
        
        # Get HSV statistics
        h_mean = np.mean(hsv[:, :, 0])
        s_mean = np.mean(hsv[:, :, 1])
        v_mean = np.mean(hsv[:, :, 2])
        
        h_std = np.std(hsv[:, :, 0])
        s_std = np.std(hsv[:, :, 1])
        v_std = np.std(hsv[:, :, 2])
        
        # Create lower and upper bounds
        lower = np.array([
            max(0, int(h_mean - 2*h_std)),
            max(0, int(s_mean - 2*s_std)),
            max(0, int(v_mean - 2*v_std))
        ])
        
        upper = np.array([
            min(179, int(h_mean + 2*h_std)),
            min(255, int(s_mean + 2*s_std)),
            min(255, int(v_mean + 2*v_std))
        ])
        
        return lower.tolist(), upper.tolist()
    
    def test_color_detection(self, frame, lower, upper):
        """Test color detection with given HSV bounds"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw detected areas
        result = frame.copy()
        for contour in contours:
            if cv2.contourArea(contour) > 50:  # Filter small noise
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.drawContours(result, [contour], -1, (0, 255, 0), 2)
        
        return result, len(contours)
    
    def run_calibration(self):
        """Main calibration interface"""
        print("=== Arcane Legends Color Calibration Tool ===")
        print("Instructions:")
        print("1. Open Arcane Legends and position it on your screen")
        print("2. Click and drag to select regions for different game elements")
        print("3. Press keys to calibrate different elements:")
        print("   'e' - Calibrate enemies")
        print("   'l' - Calibrate loot")
        print("   'p' - Calibrate portals")
        print("   'h' - Calibrate HP bar")
        print("   's' - Calibrate skill bar region")
        print("   't' - Test current color detection")
        print("   'c' - Capture new screenshot")
        print("   'q' - Quit and save configuration")
        print()
        
        cv2.namedWindow('Screen Capture')
        cv2.setMouseCallback('Screen Capture', self.select_region)
        
        # Initial capture
        self.current_frame = self.capture_screen()
        
        while True:
            # Display current frame
            display_frame = self.current_frame.copy()
            
            # Draw selected regions
            if hasattr(self, 'enemy_region') and self.enemy_region:
                x, y, w, h = self.enemy_region
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(display_frame, "ENEMY", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            if hasattr(self, 'loot_region') and self.loot_region:
                x, y, w, h = self.loot_region
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                cv2.putText(display_frame, "LOOT", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            if hasattr(self, 'portal_region') and self.portal_region:
                x, y, w, h = self.portal_region
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                cv2.putText(display_frame, "PORTAL", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            if hasattr(self, 'hp_region') and self.hp_region:
                x, y, w, h = self.hp_region
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(display_frame, "HP", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            if hasattr(self, 'skill_region') and self.skill_region:
                x, y, w, h = self.skill_region
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (255, 255, 0), 2)
                cv2.putText(display_frame, "SKILLS", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            cv2.imshow('Screen Capture', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.current_frame = self.capture_screen()
                print("Screenshot captured!")
            elif key == ord('e'):
                if self.selected_region:
                    self.enemy_region = self.selected_region
                    lower, upper = self.sample_colors_in_region(self.current_frame, self.selected_region)
                    self.calibration_data.hsv_values['enemy'] = {'lower': lower, 'upper': upper}
                    print(f"Enemy colors calibrated - Lower: {lower}, Upper: {upper}")
            elif key == ord('l'):
                if self.selected_region:
                    self.loot_region = self.selected_region
                    lower, upper = self.sample_colors_in_region(self.current_frame, self.selected_region)
                    self.calibration_data.hsv_values['loot'] = {'lower': lower, 'upper': upper}
                    print(f"Loot colors calibrated - Lower: {lower}, Upper: {upper}")
            elif key == ord('p'):
                if self.selected_region:
                    self.portal_region = self.selected_region
                    lower, upper = self.sample_colors_in_region(self.current_frame, self.selected_region)
                    self.calibration_data.hsv_values['portal'] = {'lower': lower, 'upper': upper}
                    print(f"Portal colors calibrated - Lower: {lower}, Upper: {upper}")
            elif key == ord('h'):
                if self.selected_region:
                    self.hp_region = self.selected_region
                    lower, upper = self.sample_colors_in_region(self.current_frame, self.selected_region)
                    self.calibration_data.hsv_values['hp'] = {'lower': lower, 'upper': upper}
                    print(f"HP bar colors calibrated - Lower: {lower}, Upper: {upper}")
            elif key == ord('s'):
                if self.selected_region:
                    self.skill_region = self.selected_region
                    print(f"Skill bar region set: {self.selected_region}")
            elif key == ord('t'):
                # Test color detection
                test_frame = self.current_frame.copy()
                for obj_type, colors in self.calibration_data.hsv_values.items():
                    result, count = self.test_color_detection(test_frame, colors['lower'], colors['upper'])
                    print(f"Detected {count} {obj_type} objects")
                    cv2.imshow(f'Test - {obj_type.upper()}', result)
        
        cv2.destroyAllWindows()
        self.save_configuration()
    
    def save_configuration(self):
        """Save calibration data to config file"""
        config_lines = [
            "# Auto-generated calibration data",
            "# Copy these values to config.py",
            "",
            "# HSV Color Values",
        ]
        
        # Save color values
        color_mapping = {
            'enemy': 'ENEMY_COLORS',
            'loot': 'LOOT_COLORS', 
            'portal': 'PORTAL_COLORS',
            'hp': 'HP_BAR_COLORS'
        }
        
        for obj_type, config_name in color_mapping.items():
            if obj_type in self.calibration_data.hsv_values:
                colors = self.calibration_data.hsv_values[obj_type]
                config_lines.append(f"{config_name} = {{")
                config_lines.append(f"    'lower': {colors['lower']},")
                config_lines.append(f"    'upper': {colors['upper']}")
                config_lines.append("}")
                config_lines.append("")
        
        # Save regions
        config_lines.append("# Detection Regions")
        if hasattr(self, 'hp_region'):
            config_lines.append(f"HP_BAR_REGION = {self.hp_region}")
        if hasattr(self, 'skill_region'):
            config_lines.append(f"SKILL_BAR_REGION = {self.skill_region}")
        
        # Write to file
        with open('calibration_results.py', 'w') as f:
            f.write('\n'.join(config_lines))
        
        print("Calibration saved to 'calibration_results.py'")
        print("Copy the values to your config.py file")

if __name__ == "__main__":
    calibrator = ColorCalibrator()
    calibrator.run_calibration()
