import subprocess
import os
import time
import threading
import sys

TARGET_SIZE_MB = 25
MAX_ATTEMPTS = 5
MIN_BITRATE_KBPS = 8  # absolute floor, you can lower if you like

def get_file_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)

def get_video_duration(input_file):
    """Return duration in seconds, or None on error."""
    try:
        out = subprocess.run(
            ['ffprobe','-v','error','-show_entries','format=duration',
             '-of','default=noprint_wrappers=1:nokey=1', input_file],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, check=True
        )
        return float(out.stdout.strip())
    except:
        return None

def spinner(msg, stop_event):
    chars = ['|','/','-','\\']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{msg} {chars[idx]}")
        sys.stdout.flush()
        idx = (idx + 1) % len(chars)
        time.sleep(0.1)
    sys.stdout.write("\r" + " "*(len(msg)+2) + "\r")

def convert(input_file):
    dur = get_video_duration(input_file)
    if dur is None:
        print("❌ Could not probe duration.")
        return

    # initial bitrate (bits/sec)
    raw_bitrate = (TARGET_SIZE_MB * 8 * 1024*1024) / dur
    # apply 95% margin, convert to kbps
    bitrate_kbps = max(int(raw_bitrate * 0.95 / 1000), MIN_BITRATE_KBPS)

    base = os.path.splitext(os.path.basename(input_file))[0]
    out = os.path.join(os.path.dirname(input_file), f"{base}.mp3")

    print(f"🎯 Initial target bitrate: {bitrate_kbps} kbps")

    stop = threading.Event()
    thread = threading.Thread(target=spinner, args=("🔄 Converting…", stop))
    thread.start()

    for attempt in range(1, MAX_ATTEMPTS+1):
        # convert
        try:
            subprocess.run([
                'ffmpeg','-y','-hide_banner','-loglevel','error',
                '-i',input_file,'-vn',
                '-acodec','libmp3lame','-b:a',f'{bitrate_kbps}k',
                out
            ], check=True)
        except subprocess.CalledProcessError:
            stop.set(); thread.join()
            print("\n❌ ffmpeg failed.")
            return

        size_mb = get_file_size_mb(out)
        if size_mb <= TARGET_SIZE_MB:
            stop.set(); thread.join()
            print("\n✅ Done! Output:", out, f"({size_mb:.2f} MB)")
            return

        # too big → recalc bitrate & retry
        stop.set(); thread.join()
        print(f"\n⚠️  Attempt {attempt}: {size_mb:.2f} MB > {TARGET_SIZE_MB} MB")
        ratio = TARGET_SIZE_MB / size_mb
        bitrate_kbps = max(int(bitrate_kbps * ratio * 0.95), MIN_BITRATE_KBPS)
        print(f"🔄 Retrying with {bitrate_kbps} kbps…")
        os.remove(out)

        # restart spinner
        stop.clear()
        thread = threading.Thread(target=spinner, args=("🔄 Re-converting…", stop))
        stop.clear()
        thread.start()

    # if we get here, last attempt still too big
    stop.set(); thread.join()
    final_size = get_file_size_mb(out)
    print(f"\n⚠️  Done after {MAX_ATTEMPTS} tries, but file is still {final_size:.2f} MB.")
    print("    You may need to manually lower bitrate or shorten the clip.")

if __name__ == "__main__":
    inp = input("Enter path to MP4 file: ").strip()
    if not os.path.isfile(inp):
        print("❌ File not found."); sys.exit(1)
    convert(inp)
