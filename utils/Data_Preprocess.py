from pydub import AudioSegment
import os
import csv
import argparse
import uuid

"""
    This Script is used to preprocess the LibriSpeech dataset. It searches through all *.flac files cuts and pads them to 10s.
    It creates a csv annotation to get the newly created file path and its label (speaker_id).
"""

def split_and_resample_flac(input_files, output_folder, segment_ms: int = 10000, sample_rate: int = 16000):

    new_files = []

    sound = None
    
    # Extract filename without extension
    filename = 0

    for input_file in input_files:

        # Calculate duration in milliseconds
        duration_ms = len(sound) if sound is not None else 0

        if duration_ms >= segment_ms:
            # Split the audio into segments
            for i in range(0, duration_ms, segment_ms):
                if (i + segment_ms) > duration_ms:
                    break
                # Get the segment
                segment = sound[i:i+segment_ms]
                # Construct the filename for the segment
                segment_filename = f"{filename}_segment_{i//segment_ms}.flac"
                # Save the segment to a new file in the output folder
                segment.export(os.path.join(output_folder, segment_filename), format="flac")
                new_files.append(os.path.join(output_folder, segment_filename))
                
            filename += 1

            sound = sound[duration_ms//segment_ms * segment_ms:]

        new_sound = AudioSegment.from_file(input_file)
        # Ensure the audio is in mono channel for resampling
        new_sound = new_sound.set_channels(1)
        # Set the target sample rate
        new_sound = new_sound.set_frame_rate(sample_rate)
        
        sound = sound + new_sound if sound is not None else new_sound
         
    return new_files
        

def find_audio_files(directory):
    flac_files = []
    # Iterate over files in the directory
    for file_name in os.listdir(directory):
        # Check if the file is a regular file is audio file
        file_ending = file_name.split(".")[-1]
        if os.path.isfile(os.path.join(directory, file_name)) and file_ending.lower() in ["flac", "wav", "aac"]:
            flac_files.append(os.path.join(directory, file_name))
    return flac_files


def add_csv_augmentation(file_name, entries):
    if not os.path.exists(file_name):
        
        with open(file_name, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            # Write header
            csv_writer.writerow(['filename', 'label'])
            
            # Write rows
            for filename, label in entries:
                csv_writer.writerow([filename, label])
    
    else:
        
        with open(file_name, 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write rows
            for filename, label in entries:
                csv_writer.writerow([filename, label])


def preprocess_data(data_path, dest_path, csv_augmentation):
    # Create output folder if it doesn't exist
    os.makedirs(dest_path, exist_ok=True)
    
    for idx, speaker_id in enumerate(os.listdir(data_path)):
        # Get current path to iterate over
        cur_speaker_path = os.path.join(data_path, speaker_id)
        
        # create new speaker_id
        new_speaker_id = str(uuid.uuid4())
        # create new path to save files
        new_dest = os.path.join(dest_path, new_speaker_id)
        # Create output folder if it doesn't exist
        os.makedirs(new_dest, exist_ok=False)
        
        speaker_flac_files = []

        # get all flac files from speaker
        for subdir in os.listdir(cur_speaker_path):
            cur_file_path = os.path.join(cur_speaker_path, subdir)
            # append all flac files from directory to speaker flac files
            if os.path.isdir(cur_file_path):
                speaker_flac_files += find_audio_files(directory=cur_file_path)

        # Split Flac File into segments and resample
        new_flac_files = split_and_resample_flac(speaker_flac_files, new_dest)
        entries = [(flac_file, new_speaker_id) for flac_file in new_flac_files]
        
        # add augmentation entrie
        add_csv_augmentation(csv_augmentation, entries)
                

            
# Example usage
if __name__ == "__main__":
    
    root_path = os.path.join(os.getcwd(), 'data')

    parser = argparse.ArgumentParser(description='Your CLI description here')
    parser.add_argument('-d', '--dataset', help='Specify the relative Dataset path')
    parser.add_argument('-n', '--new', help='Specify the relative Folder where to store the preprocessed data and the augmentation.csv')
    args = parser.parse_args()

    if args.dataset and args.new:
        
        data_path = os.path.join(root_path, args.dataset)
        new_data_path = os.path.join(root_path, args.new)
        AUGMENTATION_FILE = os.path.join(new_data_path, 'augmentation.csv')
        preprocess_data(data_path, new_data_path, AUGMENTATION_FILE)
    
    else:
        print('No value provided for dataset and/or new data path')
    