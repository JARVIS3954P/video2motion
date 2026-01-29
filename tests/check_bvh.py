import sys
import os

def check_bvh(file_path):
    print(f"Checking BVH file: {file_path}")
    
    if not os.path.exists(file_path):
        print("Error: File not found.")
        return False
        
    has_nan = False
    line_count = 0
    
    with open(file_path, 'r') as f:
        in_motion_section = False
        for line in f:
            line_count += 1
            if "MOTION" in line:
                in_motion_section = True
                continue
                
            if in_motion_section:
                if "Frames:" in line or "Frame Time:" in line:
                    continue
                    
                # Data lines
                parts = line.split()
                for part in parts:
                    try:
                        val = float(part)
                        if val != val: # NaN check (float('nan') != float('nan'))
                            print(f"Error: NaN found on line {line_count}")
                            has_nan = True
                            return False # Fail fast
                    except ValueError:
                        continue
                        
    if has_nan:
        print("FAILED: BVH contains NaN values.")
        return False
    else:
        print("PASSED: No NaN values found.")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_bvh.py <bvh_file>")
    else:
        check_bvh(sys.argv[1])
