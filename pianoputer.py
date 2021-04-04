#!/usr/bin/env python

from scipy.io import wavfile
import argparse
import numpy as np
import pygame
import sys,os
import warnings
import time

def speedx(snd_array, factor):
    """ Speeds up / slows down a sound, by some factor. """
    indices = np.round(np.arange(0, len(snd_array), factor))
    indices = indices[indices < len(snd_array)].astype(int)
    return snd_array[indices]


def stretch(snd_array, factor, window_size, h):
    """ Stretches/shortens a sound, by some factor. """
    phase = np.zeros(window_size)
    hanning_window = np.hanning(window_size)
    result = np.zeros(int(len(snd_array) / factor + window_size))

    for i in np.arange(0, len(snd_array) - (window_size + h), h*factor):
        i = int(i)
        # Two potentially overlapping subarrays
        a1 = snd_array[i: i + window_size]
        a2 = snd_array[i + h: i + window_size + h]

        # The spectra of these arrays
        s1 = np.fft.fft(hanning_window * a1[:,0])
        s2 = np.fft.fft(hanning_window * a2[:,0])

        # Rephase all frequencies
        phase = (phase + np.angle(s2/s1)) % 2*np.pi

        a2_rephased = np.fft.ifft(np.abs(s2)*np.exp(1j*phase))
        i2 = int(i/factor)
        result[i2: i2 + window_size] += hanning_window*a2_rephased.real

    # normalize (16bit)
    result = ((2**(16-4)) * result/result.max())

    return result.astype('int16')


def pitchshift(snd_array, n, window_size=2**13, h=2**11):
    """ Changes the pitch of a sound by ``n`` semitones. """
    factor = 2**(1.0 * n / 12.0)
    stretched = stretch(snd_array, 1.0/factor, window_size, h)
    return speedx(stretched[window_size:], factor)


def parse_arguments(rootdir):
    description = ('Use your computer keyboard as a "piano"')

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '--wav', '-w',
        metavar='FILE',
        type=argparse.FileType('r'),
        default=rootdir+'/dododo.wav',
        help='WAV file (default: dododo.wav)')
    parser.add_argument(
        '--keyboard', '-k',
        metavar='FILE',
        type=argparse.FileType('r'),    
        default=rootdir+'/typewriter.kb',
        help='keyboard file (default: typewriter.kb)')
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='verbose mode')

    return (parser.parse_args(), parser)


def main(fadeintime,fadeouttime):
    #current folder path
    rootdir = os.path.abspath(os.path.dirname(__file__))
    print(rootdir)
    # Parse command line arguments
    (args, parser) = parse_arguments(rootdir)

    # Enable warnings from scipy if requested
    if not args.verbose:
        warnings.simplefilter('ignore')

    fps, sound = wavfile.read(args.wav.name)
#    ins = 0
    tones = range(4,27)#range(-25, 25)
    sys.stdout.write('Transponding sound file... ')
    sys.stdout.flush()
    transposed_sounds = [pitchshift(sound, n) for n in tones]
    print('DONE')

    # So flexible ;)
    pygame.mixer.init(fps, -16, 1, 2048)
    # For the focus
    screen = pygame.display.set_mode((150, 150))

    keys = args.keyboard.read().split('\n')
    sounds = map(pygame.sndarray.make_sound, transposed_sounds)
    key_sound = dict(zip(keys, sounds))
    is_playing = {k: False for k in keys}
    time_up = 0
    time_down = 0
    while True:
        
        event = pygame.event.wait()

        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            key = pygame.key.name(event.key)
            

        if event.type == pygame.KEYDOWN:
            time_down = time.time()
            #print('down'+str(time_down))
#            if event.key == pygame.K_c:
#                ins += 1
#                if ins % 2 == 1:
#                    fps, sound = wavfile.read(rootdir+'/do1.wav')
#                    print('Voice now is: do1.wav')
#                else:
#                    fps, sound = wavfile.read(rootdir+'/dododo.wav')
#                    print('Voice now is: dododo.wav')
#                tones = range(4,27)#range(-25, 25)
#                sys.stdout.write('Transponding sound file... ')
#                sys.stdout.flush()
#                transposed_sounds = [pitchshift(sound, n) for n in tones]
#                print('DONE')
#                sounds = map(pygame.sndarray.make_sound, transposed_sounds)
#                key_sound = dict(zip(keys, sounds))
#                is_playing = {k: False for k in keys}
#                time_up = 0
#                time_down = 0
            
            if (key in key_sound.keys()) and (not is_playing[key]):
                print(key)
                key_sound[key].play(fade_ms=fadeintime)
                is_playing[key] = True

            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
                raise KeyboardInterrupt

        elif event.type == pygame.KEYUP and key in key_sound.keys():
            # Stops with 50ms fadeout
            print('diff'+str(abs(time_up - time_down)))
            if (abs(time_up - time_down) > 0.01):
                key_sound[key].fadeout(fadeouttime)
                is_playing[key] = False
            time_up = time.time()
            #print('up'+str(time_up))
            
               
        

if __name__ == '__main__':
    try:
        fadeintime = 50 #这个是按下按钮的反应速度参数，越大发声越慢'''
        fadeouttime = 800  #这个是延长音的参数，越大延长越多'''
        main(fadeintime,fadeouttime)
    except KeyboardInterrupt:
        print('Goodbye')
