# core/screenshot_compare.py
from PIL import Image
import numpy as np
from pathlib import Path
import uuid

def compare_screenshot(img1_bytes: bytes, img2_bytes: bytes, save_dir: Path) -> tuple[float, str]:
    """
    返回相似度 0~1，差异图路径
    """
    img1 = Image.frombytes("RGB", (1280,720), img1_bytes).convert("L")
    img2 = Image.frombytes("RGB", (1280,720), img2_bytes).convert("L")
    arr1 = np.array(img1, dtype=np.float32)
    arr2 = np.array(img2, dtype=np.float32)
    diff = np.abs(arr1 - arr2)
    diff_img = Image.fromarray(np.clip(diff*10, 0, 255).astype(np.uint8))
    uid = str(uuid.uuid4())
    diff_path = save_dir / f"{uid}_diff.png"
    diff_img.save(diff_path)
    mse = np.mean(diff)
    similarity = max(0, 1 - mse / 255.0)
    return float(similarity), str(diff_path)
