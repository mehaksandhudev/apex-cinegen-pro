"""
FFmpeg Video Stitcher Module
Fallback / alternative method to concatenate the Flow video with the CapCut outro video.
"""

import subprocess
import tempfile
from pathlib import Path
from config import OUTRO_VIDEO_PATH, OUTPUT_DIR

def stitch_videos_ffmpeg(flow_video_path: Path, output_filename: str = "stitched_final.mp4") -> Path:
    """
    Concatenates flow_video with the CapCut outro video using FFmpeg.
    Re-encodes cleanly to 1080x1920 30fps to guarantee perfect compatibility.
    """
    flow_video_path = Path(flow_video_path)
    outro_path = Path(OUTRO_VIDEO_PATH)
    output_path = OUTPUT_DIR / output_filename
    
    print(f"[FFmpeg] Stitching:\n  1. {flow_video_path.name}\n  2. {outro_path.name}\n  Output: {output_path.name}")
    
    # Filter complex to scale both videos to 1080x1920, 30fps, 44.1k/48k audio, and concat
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v0];"
        "[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v1];"
        "[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(flow_video_path),
        "-i", str(outro_path),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_path)
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[FFmpeg] Error stitching video:\n{res.stderr}")
        raise RuntimeError("FFmpeg stitching failed.")
        
    print(f"[FFmpeg] Video successfully stitched: {output_path}")
    return output_path
