"""
File conversion module for YUV420 sequences.

# SPDX-FileCopyrightText: Copyright (c) 2021 Orange
# SPDX-License-Identifier: BSD 3-Clause "New"
#
# This software is distributed under the BSD-3-Clause license.
#


Author (python API):
    Goluck Konuko <goluck.konuko@centralesupelec.fr> - PhD student, CentraleSupelec
    Date: March 01, 2022
    
Bash scripts adapted from work done by Theo Ladune and Pierre Filipe and Orange Labs for AIVC
    >Theo Ladune <theo.ladune@orange.com>
    >Pierrick Philippe <pierrick.philippe@orange.com>
"""

from argparse import ArgumentParser
import subprocess
import os, sys, shutil
from os import listdir
from os.path import isfile, join
from imageio import imread
from utils.yuv_2_png import yuv_to_png

def get_file_extension(file_path):
    return file_path.split('/')[-1].split('.')[-1]

class YUVReader:
    '''
    A video reader for yuv, y and mp4 videos-
    :: Works ONLY with videos encoded in the YUV420 format
    :: mp4 videos are first converted to yuv420 
    Returns:
        A dictionary with keys corresponding to the video sequence indices.
        ------See how it's used below------
    '''
    def __init__(self, input_file, size=None, start=0, end=0,fps=10, out_dir='out/', clean=True) -> None:
        #Video sequence characteristics -> define carefully
        self.input = input_file
        self.out_dir=out_dir
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        self.size = size
        self.start = start
        self.end = end
        self.fps =  fps
        self.clean=clean
        
        self.frames = {}
        self.n_frames = self.end-self.start
        if self.n_frames <= 0:
            print("[ERROR]: Number of frames must be greater than 0! Exiting..")
            sys.exit()
        self.ext = self._get_file_extension()
        self._read()
        
    def _get_file_extension(self):
        '''checks the file type of the video sequence'''
        return self.input.split('/')[-1].split('.')[-1]

    def _clean(self, idx):
        '''Cleans the temporary files created when readin yuv'''
        if os.path.isfile(f"{self.out_dir}/{idx}_y.png"):
            os.remove(f"{self.out_dir}/{idx}_y.png")
        if os.path.isfile(f"{self.out_dir}/{idx}_u.png"):
            os.remove(f"{self.out_dir}/{idx}_u.png")
        if os.path.isfile(f"{self.out_dir}/{idx}_v.png"):
            os.remove(f"{self.out_dir}/{idx}_v.png")

    def _read_yuv(self, input):
        '''Reads frames from .yuv videos'''
        for idx in range(self.start, self.end):
            cmd = f"bash bash_utils/yuv_to_png.sh {input} {self.out_dir} {idx} bash_utils/convert_img.py {self.size[0]} {self.size[1]}"
            subprocess.call(cmd, shell=True)
            frame = {"y": imread(f"{self.out_dir}{idx}_y.png"),
                    "u": imread(f"{self.out_dir}{idx}_u.png"),
                    "v": imread(f"{self.out_dir}{idx}_v.png")}
            self.frames[idx] = frame
        if self.clean:
            shutil.rmtree(self.out_dir)

    def _read_y(self, input):
        '''Reads .y videos'''
        for idx in range(self.start, self.end):
            cmd = f"bash bash_utils/y_to_png.sh {input} {self.out_dir} {idx} bash_utils/convert_img.py {self.size[0]} {self.size[1]}"
            subprocess.call(cmd, shell=True)
            frame = {"y": imread(f"{self.out_dir}/{idx}_y.png")}
            self.frames[idx] = frame
        if self.clean:
            shutil.rmtree(self.out_dir) 

    def _read(self):
        '''Creates the actual sequence dictionary by reading the video frame by frame
            between the defined start and end indices(must be > 0)'''
        if self.ext =='yuv':
            #read directly the yuv file returning dictionaries with y,u and v key values
            self._read_yuv(self.input)
            
        if self.ext == 'y':
            #read luma channel only
            self._read_y(self.input)

        if self.ext == 'mp4':
            #convert losslessly to yuv then read
            out_yuv = self.out_dir+self.input.split('/')[-1].split('.')[0]+'.yuv'
            subprocess.call(['ffmpeg','-nostats','-loglevel','error','-i',self.input,out_yuv, '-r',str(self.fps)])
            #read the output yuv file between the defined frames
            self._read_yuv(out_yuv)




if __name__ =="__main__":
    parser = ArgumentParser()
    parser.add_argument('--input',default='videos/akiyo_cif.yuv', help='Input file with .mp4, .y or .yuv extension')
    parser.add_argument('--size',default=[256, 256], help='[Width , Height] OPTIONAL')
    parser.add_argument('--start', default=0, help='first frame to read')
    parser.add_argument('--end', default=10,help='Last frame to encode: -1 == last possible frame')
    parser.add_argument('--fps', default=20, help='video frame rate')
    parser.add_argument('--out_dir', default='out/',help='output directory for intermediate files')
    parser.add_argument('--clean', action="store_true", help='set to delete all the intermediate files i.e. yuv frames saved as png images')
    parser.set_defaults()
    args = parser.parse_args()

    #example 1: yuv files
    '''
    args.input = 'videos/akiyo_cif.yuv'
    args.size = [352, 288]
    args.start = 0
    args.end = 10
    args.fps = 20
    '''

    #example 2: yuv file
    '''
    args.input = 'videos/example.yuv'
    args.size = [256, 256]
    args.start = 0
    args.end = 10
    args.fps = 20
    '''

    #example 2: y file
    '''
    args.input = 'videos/akiyo_cif.y'
    args.size = [352, 288]
    args.start = 0
    args.end = 100
    args.fps = 20
    '''

    #example 2: mp4 file
    '''
    args.input = 'videos/example.mp4'
    args.size = [256, 256]
    args.start = 0
    args.end = 10
    args.fps = 10
    '''
    #create a reader instance with the correct sequence parameters and settings
    reader = YUVReader(args.input, args.size, args.start, args.end, args.fps, args.out_dir, args.clean)
    #Get the dictionary of frames
    frames = reader.frames
    '''
    individual frames can be accessed via their indices
    '''
    for idx in range(args.start, args.end):
        target_frame = frames[idx]
        #the target frame is also a dictionary with key values being the channels
        #i.e. {'y':[],'u':[],'v':[]} or just {'y':[]} for the .y sequence
        y_frame = target_frame['y']
        print('Y FRAME:',y_frame.shape)
        if 'u' in target_frame:
            u_frame = target_frame['u']
            print('U FRAME:',u_frame.shape)
        if 'v' in target_frame:
            v_frame = target_frame['v']
            print('V FRAME:',v_frame.shape)
        '''You can do anything you want with the target frame HERE. cheers!'''