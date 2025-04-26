import subprocess
import os

def get_file_size(file_path):
    """Get the size of the file in MB."""
    return os.path.getsize(file_path) / (1024 * 1024)  # Size in MB

def convert_mp4_to_mp3(input_file):
    """Convert MP4 to MP3 and ensure the output file is under 25 MB."""
    # Get the duration of the video
    result = subprocess.run(['ffmpeg', '-i', input_file], stderr=subprocess.PIPE, universal_newlines=True)
    duration_line = [line for line in result.stderr.split('\n') if 'Duration' in line][0]
    duration = duration_line.split(',')[0].split(' ')[1]  # e.g., "00:01:30.00"
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

if __name__ == "__main__":
    input_file = input("Enter the path to the input MP4 file: ")  # User input for input file

    output_file = convert_mp4_to_mp3(input_file)

    if get_file_size(output_file) > 25:
        print("Warning: Output file exceeds 25 MB.")
    else:
        print(f"Conversion successful! Output file: {output_file}")
