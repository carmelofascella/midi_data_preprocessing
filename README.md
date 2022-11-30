# MIDI Data preprocessing

This repository hosts the scripts to preprocess MIDI files composed of two tracks: ideally one corresponding to a melody and the other one corresponding to a harmony.

The goal of this processing phase was to create a dataset to finetune the pre-trained models of `musicautobot` (https://github.com/bearpelican/musicautobot)

The folder `data/input_dataset` contains two entries of the wikifonia dataset, converted into midi files, as an example.

The final processed midi files are saved in the folder `data/preprocessed_dataset`.

Rules applied in the processing phase:

- If the midi file doesn't contain two track, the file is discarded.
- If there is a pitch in the chord track that is out of the piano range, the song is descarded.
- If the pitches of two consecutive notes in the melody is higher than an octave, the song is discarded.
- If there is one pitch in the melody out of the range (24, 76), the song is discarded.
- If the amount of rest in the melody track is more than the 25% of the total song duration, the song is discarded.
- If the amount of rest in the chord track is more than the 25% of the total song duration, the song is discarded.

## 1. Setup

`pip install -r requirements.txt `

## 2. Execution

`cd script/`

`python preprocess_dataset.py`
