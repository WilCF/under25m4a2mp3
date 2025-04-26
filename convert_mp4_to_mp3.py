import subprocess
import os

def get_file_size(file_path):
    """Get the size of the file in MB."""
    return os.path.getsize(file_path) / (1024 * 1024)  # Size in MB

def convert_mp4_to_mp3(input_file):
    """Convert MP4 to MP3 and ensure the output file is under 25 MB."""
    try:
        # Get the duration of the video
        result = subprocess.run(['ffmpeg', '-i', input_file], stderr=subprocess.PIPE, universal_newlines=True)
        
        # Check for errors in the FFmpeg output
        if result.returncode != 0:
            print("Error: FFmpeg encountered an issue.")
            print(result.stderr)
            return None

        # Extract the duration from the output
        duration_line = [line for line in result.stderr.split('\n') if 'Duration' in line]
        if not duration_line:
            print("Error: Could not find duration in FFmpeg output.")
            return None
        
        duration = duration_line[0].split(',')[0].split(' ')[1]  # e.g., "00:01:30.00"
        hours, minutes, seconds = map(float, duration.split(':'))
        total_seconds = hours * 3600 + minutes * 60 + seconds

        # Calculate the target bitrate to keep the file under 25 MB
        target_size_mb = 25
        target_bitrate = (target_size_mb * 8 * 1024 * 1024) / total_seconds  # in bits per second

        # Create the output file name by replacing the extension
        output_file = os.path.splitext(input_file)[0] + '.mp3'

        # Convert the video to audio with the calculated bitrate
        subprocess.run([
            'ffmpeg', '-i', input_file, '-b:a', f'{int(target_bitrate)}k', output_file
        ])

        return output_file

    except Exception
