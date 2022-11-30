"""
Given a dataset of midi files composed of two tracks (melody and chords),
it returns a new folder with filtered songs.

Rules:

- If the midi file doesn't contain two track, the song is discarded
- If there is a pitch in the chord track out of the piano range, the song is descarded
- If the pitches of two consecutive notes in the melody is higher than an octave, the song is discarded.
- If there is one pitch in the melody out of the range (24, 76), the song is discarded.
- If the amount of rest in the melody track is more than the 25% of the total song duration, the song is discarded.
- If the amount of rest in the chord track is more than the 25% of the total song duration, the song is discarded.
"""

import glob
import os
import pretty_midi
import numpy as np
import argparse

#argument parser
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input_dataset_folder", default="../data/input_dataset", help="folder which contains the dataset we want to preprocess")
ap.add_argument("-o", "--output_dataset_folder", default="../data/processed_dataset", help="folder where we save the output result of the processing")
ap.add_argument("-r", "--pause_thresh_perc", default=25, help="")
ap.add_argument("-t", "--out_of_range_perc", default=0, help="")
args = vars(ap.parse_args())
input_directory = args["input_dataset_folder"]
output_directory = args["output_dataset_folder"]
pause_thresh_perc = args["pause_thresh_perc"]
tresh_out_of_range_perc = args["out_of_range_perc"]



def read_midi_file(midi_file):
    """
        Read a midi file and outputs a midi list

        Parameters:
            midi_file: path of a midi file
        
        Return:
            out: midi dictionary. Each key is a track; the values for each keys are in the format [start,end,pitch]

    """

    midi_data = pretty_midi.PrettyMIDI(midi_file)
    out = {}

    pitches = []
    # read input
    for track_index, instrument in enumerate(midi_data.instruments):

        out[track_index] = []

        for note in instrument.notes:
            note_pitch = note.pitch 
            note_start = note.start
            note_end = note.end

            curr_note_event = [note_start, note_end, note_pitch]
            
            out[track_index].append(curr_note_event)

            pitches.append(note_pitch)

        out[track_index] = sorted(out[track_index], key=lambda x: (x[0], x[2]))


    return out


def write_midi_file(midi_list, song_name):
    """
        Write a midi file with the info contained in the midi list

        Parameters:
            midi_list = list of midi notes in the format [start, end, pitch]
            song_name = name of the saved midi file

    """

    out_midi = pretty_midi.PrettyMIDI()
    piano_program = pretty_midi.instrument_name_to_program('Acoustic grand piano')
    
    for track_index in midi_list.keys():
        piano = pretty_midi.Instrument(program=piano_program)
        current_midi_track = midi_list[track_index]
    
        for note in current_midi_track:
            pretty_midi_note = pretty_midi.Note(velocity=127, pitch=note[2], start=note[0], end=note[1])
            piano.notes.append(pretty_midi_note)
    
        out_midi.instruments.append(piano)
    
    print(output_directory + "/" + song_name)   
    out_midi.write(output_directory + "/" + song_name)  

       


def cut_midi_file(midi_list):
    """
    This function takes as input a midi_list, and cuts the midi tracks in order to have the same end time for each track
    First, we find the longest track, adn the end time of the shortest one, which will be the end time of the output midi file;
    Then, we cut the short track following these rules:
    - if a certain note starts after the end of the other track, we remove that note
    - if a certain note starts before the end of the other track, but it ends after, we set its new end time
    """

    first_track_end_time = midi_list[0][-1][1]
    second_track_end_time = midi_list[1][-1][1]

    list_end_times = [first_track_end_time,second_track_end_time]

    cut_song_end_time = min(list_end_times)

    track_to_cut_idx = list_end_times.index(max(list_end_times))

    track_to_cut = midi_list[track_to_cut_idx]



    n=0
    while (n<len(track_to_cut)):

        #if the note starts after the end of the other track
        if(track_to_cut[n][0] >= cut_song_end_time):
            midi_list[track_to_cut_idx].pop(n)
            n = n-1


        #if a certain note starts before the end of the other track, but it ends after
        else:
            
            if(track_to_cut[n][1] > cut_song_end_time):
                midi_list[track_to_cut_idx][n][1] = cut_song_end_time
        n = n+1

    return midi_list




def preprocess_dataset(input_directory):

    midi_files = glob.glob(input_directory+"/*.mid", recursive=True)

    num_discarted_songs = 0
    num_discarted_songs_out_of_range = 0
    num_discarted_songs_above_octave = 0
    num_discarted_songs_chords_out_of_range = 0
    num_discarted_songs_num_tracks = 0
    num_discarted_songs_rest_chords = 0
    num_discarted_songs_rest = 0
    
    for idx_file, midi_file in enumerate(midi_files):

        count_notes = 0
        count_notes_out_of_range = 0
        pitches = []

        curr_pitch = 0
        prev_pitch = ""
        prev_note_end = 0
        prev_note_start = 0

        one_octave_apart_flag = False
        chord_out_of_range_flag = False

        rest_amount_sec = 0
        rest_amount_sec_chords = 0

        #read file
        midi_list = read_midi_file(midi_file)

        song_name = midi_file[midi_file.rfind("/")+ 1 :]

        #check number of tracks
        if(len(midi_list)!=2):
            num_discarted_songs_num_tracks +=1
            print("File discarted!! - Current file doesn't contain 2 tracks. ")
            continue

        else:
            #cut track
            out = cut_midi_file(midi_list)


        #notes in the chord track
        for i, notes in enumerate(out[1]):
            curr_note_start = notes[0]
            curr_note_end = notes[1]
            curr_pitch = notes[2]

            #if notes out of the piano range
            if(curr_pitch<21 or curr_pitch > 108):
                chord_out_of_range_flag = True
                num_discarted_songs_chords_out_of_range += 1
                break

            if((curr_note_start > prev_note_start) and (curr_note_end > prev_note_end)):
                rest_amount_sec_chords += curr_note_start - prev_note_end

            prev_note_end = curr_note_end
            prev_note_start = curr_note_start
        

        if(chord_out_of_range_flag):
            print("File discarted!! - More than 1 note in the chord track is out of range ")
            continue

        ########################################

        prev_note_end = 0
        prev_note_start = 0
        #notes in the melody track
        for notes in out[0]:
            curr_note_start = notes[0]
            curr_note_end = notes[1]
            curr_pitch = notes[2]


            #4 octave range starting from C1
            if(curr_pitch<24 or curr_pitch > 72):
                count_notes_out_of_range += 1

            pitches.append(curr_pitch)

            #let's consider only consecutive notes
            if((curr_note_start > prev_note_start)):
                
                #rest calculation if also the end is different
                if(curr_note_end > prev_note_end):
                    rest_amount_sec += curr_note_start - prev_note_end

                #pitch difference calculation starting from the second note in the list
                if(prev_pitch!=""):
                    diff_pitches = np.abs(curr_pitch - prev_pitch)
                
                    if(diff_pitches>12):
                        one_octave_apart_flag = True
                        break
            
            prev_pitch = curr_pitch
            prev_note_end = curr_note_end
            prev_note_start = curr_note_start

            count_notes+=1

        max_pitch = max(pitches)
        min_pitches = min(pitches)
        percentage_out_of_range = count_notes_out_of_range/count_notes
        song_duration_sec = notes[1]
        rest_percentage = (rest_amount_sec/song_duration_sec)*100
        rest_percentage_chords = (rest_amount_sec_chords/song_duration_sec)*100
                  
        print("Max pitch: ", max_pitch)
        print("Min pitch: ", min_pitches)
        print("Percentage notes out of range: ", percentage_out_of_range)
        print("Rest percentage in the melody track: ", rest_percentage)
        print("Rest percentage in the chord track: ", rest_percentage_chords)

        #check octave flag
        if(one_octave_apart_flag):
            print("File discarted!! - Difference of pitches is higher than 1 octave ")
            num_discarted_songs_above_octave +=1
            continue
        
        #check range
        if(percentage_out_of_range > tresh_out_of_range_perc):
            num_discarted_songs_out_of_range+=1
            print("File discarted!! - More than 1 note out of range ")
            continue

        #check rest percentage
        if((rest_percentage > pause_thresh_perc)):
            num_discarted_songs_rest +=1
            print("File discarted!! - Rest percentage above the minimum allowed (25%) ")
            continue
        
        #check rest percentage in the chord track
        if(rest_percentage_chords > pause_thresh_perc):
            num_discarted_songs_rest_chords +=1
            print("File discarted!! - Rest percentage in the chord track above the minimum allowed (25%) ")
            continue

        write_midi_file(out, song_name)


    print("\n\n\n")

    num_songs = idx_file+1
    num_discarted_songs = num_discarted_songs_out_of_range + num_discarted_songs_above_octave + num_discarted_songs_rest + num_discarted_songs_chords_out_of_range + num_discarted_songs_num_tracks + num_discarted_songs_rest_chords
    accepted_songs = num_songs-num_discarted_songs
    accepted_songs_perc = (accepted_songs/num_songs) * 100

    print("N° discarted songs [more than one pitch in the chord track is out of range] : ", num_discarted_songs_chords_out_of_range)
    print("N° discarted songs [consecutive pitches difference above an octave] : ", num_discarted_songs_above_octave)
    print("N° discarted songs [more than one pitch out of range] : ", num_discarted_songs_out_of_range)
    print("N° discarted songs [amount of rest above the threshold] : ", num_discarted_songs_rest)
    print("N° discarted songs [amount of rest in the Chord Track above the threshold] : ", num_discarted_songs_rest_chords)
    print("N° discarted songs [num of tracks is not 2] : ", num_discarted_songs_num_tracks)
    
    print("N° discarted songs: ", num_discarted_songs)
    print("Num songs: ", num_songs)
    print("Accepted songs: ", accepted_songs)
    print("Accepted songs[%]: ", accepted_songs_perc)

    return


if __name__ == '__main__':

    os.makedirs(output_directory, exist_ok = True)
    print("Created: ", output_directory)

    preprocess_dataset(input_directory)

