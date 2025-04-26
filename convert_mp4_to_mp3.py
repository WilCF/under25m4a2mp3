import subprocess
import os
import time
import threading
import sys

def get_file_size(file_path):
    """Get the size of the file in MB."""
    return os.path.getsize(file_path) / (1024 * 1024)

def get_video_duration(input_file):
    """Get the duration of the video in seconds."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', input_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"❌ Error getting duration: {e}")
        return None

def show_spinner(message, stop_event):
    """Simple spinner animation."""
    spinner = ['|', '/', '-', '\\']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{message} {spinner[idx % len(spinner)]}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.2)
    sys.stdout.write("\r")  # Clear spinner line after stop

def convert_mp4_to_mp3(input_file):
    """Convert MP4 to MP3 and ensure the output file is under 25 MB."""
    try:
        # Calculate video duration
        total_seconds = get_video_duration(input_file)
        if total_seconds is None:
            print("❌ Could not get video duration.")
            return None

        # Target file size
        target_size_mb = 25
        target_bitrate = (target_size_mb * 8 * 1024 * 1024) / total_seconds  # bits per second
        target_bitrate_kbps = max(int(target_bitrate / 1000), 64)  # at least 64 kbps

        # Create output filename by replacing extension with .mp3
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_dir = os.path.dirname(input_file)
        output_file = os.path.join(output_dir, f"{base_name}.mp3")

        print(f"🎯 Target bitrate: {target_bitrate_kbps} kbps")
        print(f"🎶 Output file will be: {output_file}")

        # Start spinner
        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=show_spinner, args=("🔄 Converting...", stop_event))
        spinner_thread.start()

        # Run ffmpeg conversion
        subprocess.run([
            'ffmpeg', '-y', '-i', input_file,
            '-vn', '-acodec', 'libmp3lame',
            '-b:a', f'{target_bitrate_kbps}k',
            output_file
        ], check=True)

        # Stop spinner
        stop_event.set()
        spinner_thread.join()

        print("✅ Conversion completed!")

        return output_file

    except subprocess.CalledProcessError as e:
        print("❌ Error during ffmpeg conversion.")
        print(e)
        return None
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return None

if __name__ == "__main__":
    input_file = input("Enter the path to the input MP4 file: ").strip()

    if not os.path.isfile(input_file):
        print("❌ Input file does not exist.")
        exit(1)

    output_file = convert_mp4_to_mp3(input_file)

    if output_file:
        size_mb = get_file_size(output_file)
        if size_mb > 25:
            print(f"⚠️ Warning: Output file is {size_mb:.2f} MB, exceeds 25 MB.")
        else:
            print(f"✅ Conversion successful! Output file: {output_file} ({size_mb:.2f} MB)")
