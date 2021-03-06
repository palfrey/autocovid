#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lsoa_plot.py


This script generates a series of .PNG files (which can be converted into a 
video using FFMPEG etc) from the weekly LSOA data file, available from this 
link: https://coronavirus.data.gov.uk/downloads/lsoa_data/LSOAs_latest.csv

This file contains the weekly number of cases in English LSOAs in which the 
number of cases is 3 or greater (2 or fewer are denoted in the file by -99).

The LSOA index names are cross-referenced with X-Y coordinates from the
"Lower Layer Super Outer Areas (December 2011) Population Weighted Centroids"
data-set, available from:
    
https://geoportal.statistics.gov.uk/datasets/b7c49538f0464f748dd7137247bbc41c_0

Based on github.com/jah-photoshop/lsoa-plot

MIT License

Copyright 2020 - @jah-photoshop

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

@author: @jah-photoshop

"""

#  Tested on Ubuntu (20.04) with Python 3.8.2
#  Prerequisits:  
#  sudo apt install imagemagick ffmpeg
#  pip install matplotlib csv
  
import csv, math, os, sys
import matplotlib.pyplot as plt
import random
from datetime import datetime, timedelta

print("Covid LSOA dataset file parser   -   version 1.2   -   @jah-photoshop Sept 2020")
print("")
print("This script reads from the LSOA data csv and converts to regional percentage")
print("statistics, as published on coronavirus.data.gov.uk")
print("")

#Some parameters that may want to be tweaked...
debug = False               # Set to True to print extended debug information whilst processing
size_factor = 10             # The size of the dots.  Bigger number, bigger dots.
dot_out_colour = "#ff5500"  # The RGB colour of the new outbreak dots.         Bright Red="#ff0000"
dot_new_colour = "#ee4400"  # The RGB colour of the new outbreak dots.         Bright Red="#ff0000"
dot_his_colour = "#dd3A00"  # The RGB colour of the historical outbreak dots.  Deeper Red="#dd0000"
weekly_decay = 0.5          # The factor which dot size reduces each week 
framerate = 24              # Video FPS (for ffmpeg string)
edgewidth = 2.0             # The width of the stroke (outside of dot) for new cases in pixels

f=plt.figure(figsize=(12,14),dpi=140,frameon=False) 


#Parse a CSV file and read data lines into list
def read_file(filename):
    data = []
    if(debug): print ("Opening file %s" % (filename))
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
          data.append(row)
    if(debug): print(f'Processed {len(data)} lines.')
    return (data)

#There has been a problem...
def fail(message):
    print("There has been an error:")
    print(message)
    sys.exit()

#Create output paths
output_path         = input("Enter output path [default: plots/lsoa]             : ") or "plots/lsoa"
if os.path.exists(output_path): fail("Output path already exists (%s)" % (output_path))
os.mkdir(output_path)

#Get filename for map dataset

#To download lsoa map data file:
#wget https://opendata.arcgis.com/datasets/b7c49538f0464f748dd7137247bbc41c_0.csv?outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D -O lsoa_map.csv
load_map_data =       input("Do you wish to download map data (yes\\no [default]) : ") or "no"
if(load_map_data.startswith('y')):
    os.system("wget https://opendata.arcgis.com/datasets/b7c49538f0464f748dd7137247bbc41c_0.csv?outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D -O data/lsoa_map.csv")

lsoa_map_filename   = input("Enter map filename [default: data/lsoa_map.csv]     : ") or "data/lsoa_map.csv"

if not os.path.isfile(lsoa_map_filename): fail("Map file not found (%s)" % (lsoa_map_filename))

map_data = read_file(lsoa_map_filename)

x_coord = []
y_coord = []
lsoa_name = []
for count,line in enumerate(map_data):
    #Unfortunately the LSOA dataset is England only; ignore Welsh (and other) entries 
    if line[3].startswith('E'):
        try:
            x_coord.append(float(line[0]))
            y_coord.append(float(line[1]))
            lsoa_name.append(line[3])
        except:
            print("Error on line %d:%s" % (count,line))
            
lsoa_data_filename   = input("Enter lsoa data filename [default: data/lsoa.csv]   : ") or "data/lsoa.csv"
if not os.path.isfile(lsoa_data_filename): fail("Data file not found (%s)" % (lsoa_data_filename))

data = read_file(lsoa_data_filename)
if(debug): print("LSOA data loaded, %d lines" % len(data))

#Number of video\still frames to produce for each week of data
frames_per_day   = int(input("Frames per day [default: 6]                         : ") or "6")

#Decay rate for existing cases.  Set so size of historical cases halves every week
decay_rate = math.pow(weekly_decay,1.0 / (frames_per_day * 7.0))

#The LSOA data files start at week 5 and add a new column each week
number_of_weeks = len(data[0]) - 2

#We will ignore the first few weeks as there are zero LSOAs with 3+ cIases
started = False

#Historical outbreaks stores a list of outbreaks from previous frames days
historical_outbreaks = []

frame_count = 0
previous_week_count = 0
#Step through data set one week at a time
for week in range(number_of_weeks):
    #Title and date strings are displayed on each frame
    title_string = "Week %d" % (week+5)
    s_date = datetime(2020,2,4)
    s_date += timedelta(days = (7 * week))

    date_string = s_date.strftime("%B %d") #Format date to [Month Day] eg September 22
    
    print("Processing %s [%d of %d]" % (data[0][week+2],week+1,number_of_weeks))
    
    #Weekly outbreaks stores a list of all the coords + sizes of outbreaks in a week
    weekly_outbreaks = []
    future_week_count = 0
    last_week = (week + 1 == number_of_weeks)
    for line in data:
        #Filter out the header line and unidentified LSOAs
        if(line[0]!='lsoa11_cd' and line[0]!='xxxxxxxxx'):
            try:
                cases = int(line[week+2])
                if cases > 2: #Only LSOAs with 3 or more cases are reported...
                    xref = lsoa_name.index(line[0])
                    outbreak = [cases,x_coord[xref],y_coord[xref]]
                    weekly_outbreaks.append(outbreak)
                #Version 1.2 - Added blending between weeks.  Calculate number of weekly outbreaks from previous and next week
                if not last_week:
                    f_cases = int(line[week+3])
                    if f_cases > 2: future_week_count += 1
            except:
                print("Error on line:%s" % (line))

    week_count = len(weekly_outbreaks)
    if last_week:
        future_week_count = week_count
    print("Entries this week: %d [previous: %d  next: %d]" % (week_count,previous_week_count,future_week_count) )
    
    #Version 1.2 - This is where simple linear interpolation based on previous,current and next weeks means is used
    #Relative values are calculated for each step, then normalised to ensure all cases are added
    #Should provide a lot smoother graph with less obvious big steps at each week
    if(week_count > 0):
        mid_point_rel = 1.0
        start_point_rel = ((week_count + previous_week_count) / 2.0 ) / week_count
        end_point_rel = (( (future_week_count - week_count) / 2.0) / week_count) + 1
        if(debug):print("SPR: %f  EPR: %f" %(start_point_rel,end_point_rel))
        rel_list = []
        rmp = int(frames_per_day * 3.5)
        smp = (frames_per_day * 7) - rmp 
        
        if (rmp > 0): rmp_step = (1 - start_point_rel) / rmp
        smp_step = (1 - end_point_rel) / smp
        
        for i in range(rmp):
            rel_list.append(start_point_rel + (i * rmp_step))
        for i in range(smp):
            rel_list.append(1.0 - (i * smp_step))
        normalised_rel = [((val / sum(rel_list)) * week_count) for val in rel_list]
        if(debug):print(normalised_rel)

        added=0
        t_count=0.0
        normalised_list = []
        for i in range((frames_per_day * 7) -1):
            t_count+=normalised_rel[i]
            int_val = int(t_count)
            normalised_list.append(int_val - added)
            added = int_val
        normalised_list.append(week_count - added)
           
#        normalised_list = [round(val) for val in normalised_rel]
#        normalised_list[frames_per_week-1]=week_count-sum(normalised_list[:-1])
        if(debug):print("Normalised list [%d]: %s" % (sum(normalised_list),normalised_list))
    
    previous_week_count = week_count

    #Don't actually start plotting frames until there are outbreaks to show...
    if not started:
        if len(weekly_outbreaks) > 0: started=True
        
    #Plotting frames has begin: generate frame data
    if started:
        #Shuffle the weekly outbreaks; if we don't do this dots will be drawn in clusters based on the layout of the data file
        random.shuffle(weekly_outbreaks)
        case_index = 0
        r_tot = 0
        #Divide the week into a number of frames
        for frame in range(frames_per_day * 7):
             #A list of the new outbreaks to display in this frame
             frame_outbreaks = []
             #r_tot += len(weekly_outbreaks) / float(frames_per_week)
             r_tot += normalised_list[frame]
             while(case_index < int(r_tot)):
                 #print("Case index:%d R_tot:%f W_O_length:%d" % (case_index,r_tot,len(weekly_outbreaks)))
                 af = weekly_outbreaks[case_index]
                 af.extend([0])
                 if(case_index < len(weekly_outbreaks)): frame_outbreaks.append(af)
                 case_index += 1
             frame_count += 1  
             #Update historical frames
             del_entry = []
             for count, entry in enumerate(historical_outbreaks):
                 #Each frame we reduce diameter of historical dot and increase transparency as it gets older
                 m_val = entry[0] * decay_rate
                 if(m_val < 0.6):
                     del_entry.append(count)
                 historical_outbreaks[count][0] = m_val
                 #Column 3 holds the age of the case in weeks; cases get progressively more transparent over 2 week period
                 historical_outbreaks[count][3] += (1.0 / (frames_per_day * 7))
             #Purge entries with diameter below minimum size.  Small outbreaks will dissapear after ~10 days, larger ones a bit longer 
             for del_line in del_entry:
                 del historical_outbreaks[del_line]
             print("Frame %d: New entries %d  Historical entries %d" % (frame_count,len(frame_outbreaks),len(historical_outbreaks)))
             #Generate plot
             #plt.figure(figsize=(11,14),frameon=False)
             #f=plt.figure(figsize=(12,14),dpi=113.72,frameon=False) 
             plt.axis([133000,658000,10600,655000])
             #plt.text(550000,595000,title_string, horizontalalignment='center',fontsize=26)
             #Version 1.3: Added optional daily update to date string
             s_date = datetime(2020,2,3)
             s_date += timedelta(days = ((7 * (week - 1)) + int( float(frame) / frames_per_day)))
             date_string = s_date.strftime("%B %d") #Format date to [Month Day] eg September 22
             #plt.text(550000,576000,date_string, horizontalalignment='center', style='italic',fontsize=15)
             #Plot historical outbreaks first
             x_h = []
             y_h = []
             s_h = []
             #Subdivide historical entries into [frames_per_day * 14] different lists based on age.  Each plotted in successively lower alpha
             lim = frames_per_day * 14
             for i in range(lim):
                 x_h.append([])
                 y_h.append([])
                 s_h.append([])
             for entry in historical_outbreaks:
                 a_hs = entry[3] * frames_per_day * 7
                 a_hi = int(a_hs)
                 if(a_hi > (lim-1)): a_hi=lim-1
                 x_h[a_hi].append(entry[1])
                 y_h[a_hi].append(entry[2])
                 s_h[a_hi].append(entry[0] * size_factor)
             for j in range(lim):
                 #Reverse order so oldest outbreaks are drawn first
                 i = lim - (j + 1)
                 #Alpha value (transparency) 
                 a_val = 1.0 - ( (i + 1) / float(lim+1) ) #Alpha ranges from eg 0.93 to 0.06 over 2 week period
                 s_a_val = a_val * a_val
                 if(len(x_h[i])>0): 
                     #print("%d:%f" % (i,s_a_val) )
                     plt.scatter(x_h[i],y_h[i],s=s_h[i],c=dot_his_colour,alpha=s_a_val )
             #Now plot current outbdot_new_colour = "#ff0000"  # The RGB colour of the new outbreak dots.         Bright Red="#ff0000"
             x_c = []
             y_c = []
             s_c = []
             for entry in frame_outbreaks:
                 x_c.append(entry[1])
                 y_c.append(entry[2])
                 s_c.append(entry[0] * size_factor)
             plt.scatter(x_c,y_c,s=s_c,c=dot_new_colour,edgecolors=dot_out_colour,linewidths=edgewidth)
             #plt.scatter(x_coord,y_coord,s=3,c="#0044ff")  #Plot all LSOAs (for aligning map etc)
             plt.axis('off')
             #Create filenames
             #sfn = "frame%04d.png" % (frame_count)
             sfn = s_date.strftime("%Y%m%d") + ("-%03d.png" % (frame % frames_per_day))
             ofn = output_path + os.path.sep + sfn
             #rfn = merged_path + os.path.sep + sfn
             #Save the plot as transparent PNG (tight bounding box removes most of border)
             plt.savefig(ofn, bbox_inches='tight')
             os.system('convert %s -resize 918x1040\! %s' % (ofn,ofn))        
             #Add the new outbreaks to the list of historical outbreaks for future frames
             historical_outbreaks.extend(frame_outbreaks)
             #Call convert (from imagemagick package) to create composite of background and new image
             #os.system('convert %s %s -composite +antialias %s' % (background_filename,ofn,rfn))
             #Clear the figure
             f.clf()
             #plt.close(f)
#             
##Create two seconds worth of duplicate frames at the end of the sequency 
#print("Standard frames completed, duplicating final frame")
#for i in range(framerate * 2):
#     nsfn = "frame%04d.png" % (frame_count + i + 1)
#     os.system('cp %s %s' % (rfn,merged_path + os.path.sep + nsfn))
#print("Generating video using FFMPEG...")
#ffmpeg_line = ("ffmpeg -framerate %d -pattern_type glob -i '" % (framerate)) + merged_path + os.path.sep+ "*.png' -c:v libx264 -r 30 -pix_fmt yuv420p "+output_path+os.path.sep+"out.mp4"
#print(ffmpeg_line)
#os.system(ffmpeg_line)        
#
#
#             