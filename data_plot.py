#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_plot.py


This script generates a series of .PNG files (which can be converted into a 
video using FFMPEG etc) from the combined data file.

                                              
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

print("Covid Data             Plotter   -   Version 1.0   -   @jah-photoshop Sept 2020")
print("")
print("This script reads from the combined data csv and plots as series of PNG")
print("")

#Some parameters that may want to be tweaked...
debug = False            # Set to True to print extended debug information whilst processing

start_date = datetime(2020,8,1)
surpress_days = timedelta(days=3)
plt.rcParams.update({'font.size': 26})
plt.rcParams.update({'axes.linewidth': 0})

f=plt.figure(figsize=(36,5),dpi=72,frameon=False) 
a_bar_col = "#2266AA"
a_line_col = "#EE3333"
a_edge_col = "#5599CC"
i_bar_col = "#CCCCE0"
i_line_col = "#FFBBBB"
i_edge_col = "#BBBBDD"


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
output_path         = input("Enter output path   [default: plots]           : ") or "plots"
if os.path.exists(output_path): fail("Output path already exists (%s)" % (output_path))
os.mkdir(output_path)

cases_filename   = input("Enter data filename [default: data/england.csv]: ") or "data/england.csv"

if not os.path.isfile(cases_filename): fail("Combined data file not found (%s)" % (cases_filename))


#Background image is merged with each output frame using convert (imagemagick)
background_filename   = input("Background image filename [default: bg.png]    : ") or "bg.png"
if not os.path.isfile(background_filename): fail("Background image file not found (%s)" % (background_filename))


data = read_file(cases_filename)

dates = []
end_date = start_date

def annotate_picture(filename,list_of_annotations):
    annotate_string = "convert %s -gravity SouthEast -pointsize 23 " % filename
    for annotation in list_of_annotations:
        if(annotation[3]):  #Right justified for numerical entries
            sub_string =  " -gravity SouthEast -pointsize 23 -stroke '#000C' -strokewidth 2 -annotate +%d+%d '%s' " % (annotation[0],annotation[1],annotation[2])
            sub_string += "-stroke none -fill white -annotate +%d+%d '%s' " % (annotation[0],annotation[1],annotation[2])
        else:
            sub_string =  " -gravity SouthWest -pointsize 44 -stroke '#000C' -strokewidth 2 -annotate +%d+%d '%s' " % (annotation[0],annotation[1],annotation[2])
            sub_string += "-stroke none -fill white -annotate +%d+%d '%s' " % (annotation[0],annotation[1],annotation[2])           
        annotate_string += sub_string
    annotate_string += filename
    #print(annotate_string)
    os.system(annotate_string)
        
def get_ra(list_in):
    ra = []
    for count,entry in enumerate(list_in):
        cra = 0
        for k in range(7):
            if count + k < len(list_in): cra += list_in[count+k]
        dra = cra / 7.0
        ra.append(dra)
    return ra

for count,line in enumerate(data):
    if count > 0:
        try:
            e_date = datetime.strptime(line[0],"%Y-%m-%d")
            if (e_date > end_date): end_date = e_date
            dates.append(e_date)
        except:
            print("Error on line %d:%s" % (count,line))
            
#print(dates)
#print(cases)
no_days = (end_date - start_date - surpress_days).days
charts_to_plot = ['Cases','Admissions','Patients','Ventilated','Deaths']
headers = data[0]
plot_list = []
for chart in charts_to_plot:
    plot_list.append(headers.index(chart))


for day in range(no_days):
#for day in range(1):
    annotation_list = []
    day_d = timedelta(days=day)
    c_day = start_date + day_d
    print ("Generating plots for %s" % (c_day.strftime("%Y-%m-%d")))
    ofn_list = []
    for c_c, column_ix in enumerate(plot_list):
        chart = data[0][column_ix]
        pre_cases = []
        post_cases = []
        pre_dates = []
        post_dates = []
        pre_avs = []
        post_avs = []
        cases = []
        c_max = 0
        for line in (data[1:]):
            if(line[column_ix] == ''): 
                    cases.append(0)
            else:
                    e_cases = int(line[column_ix])
                    cases.append(e_cases)
        avs = get_ra(cases)
        for count,entry in enumerate(dates):
            if entry>=start_date and cases[count]>c_max: c_max = cases[count]

            if start_date + day_d > entry:
                pre_cases.append(cases[count])
                pre_dates.append(entry)
                pre_avs.append(avs[count])
            else:
                post_cases.append(cases[count])
                post_dates.append(entry)
                post_avs.append(avs[count])
        plt.axis([start_date-timedelta(hours=36),end_date-surpress_days+timedelta(hours=12),0,c_max*1.02])
        ax=plt.gca()
        pad_w= -10 - ( len("%d" % c_max) * 14)
        ax.tick_params(axis="y", direction="in", pad=pad_w)
        ax.tick_params(axis="x", direction="in")
        for tick in ax.xaxis.get_major_ticks():
            tick.label1.set_visible(False)
        yticks = ax.yaxis.get_major_ticks()
        yticks[0].label1.set_visible(False)
        plt.bar(pre_dates,pre_cases,width=0.6,color=a_bar_col,edgecolor=a_edge_col,linewidth=0.72)
        plt.plot(pre_dates,pre_avs,color=a_line_col,linewidth=6)
        plt.bar(post_dates,post_cases,width=0.6,color=i_bar_col,edgecolor=i_edge_col,linewidth=0.72)
        plt.plot(post_dates,post_avs,color=i_line_col,linewidth=6)
        plt.axvline(x=c_day-timedelta(hours=16), color="#552255", ls=':', lw=3)
        #plt.text(start_date+timedelta(days=80),c_max*0.87, "Daily Figure:", horizontalalignment='left', fontsize=34)
        #plt.text(start_date+timedelta(days=80),c_max*0.70,"7-day Average:", horizontalalignment='left', fontsize=34)
        #plt.text(start_date+timedelta(days=120),c_max*0.87, "%d" % int(pre_cases[0]), horizontalalignment='right', fontsize=34,weight='bold')
        #plt.text(start_date+timedelta(days=120),c_max*0.70,"%d" % int(pre_avs[0]), horizontalalignment='right', fontsize=34,weight='bold')
        annotation_list.append([1220,880 - (c_c * 174),"%d" % int(pre_cases[0]),True])
        annotation_list.append([990,880 - (c_c * 174),"%d" % int(pre_avs[0]),True])        
        ofn = output_path + chart + ".png"
        ofn_list.append(ofn)
        plt.savefig(ofn, bbox_inches='tight',transparent=True)
        f.clf()
        #Call convert (from imagemagick package) to resize image to 900x124 pixels
        os.system('convert %s -trim -resize 900x124\! %s' % (ofn,ofn))        
    frame_name = output_path + os.path.sep + c_day.strftime("%Y%m%d.png")
    #Call convert to merge all frames
    print("Compositing images")
    os.system('cp %s %s' % (background_filename,frame_name))
    for count,figfn in enumerate(ofn_list):
        os.system('composite -geometry +30+%d %s %s %s' % (200 + (count * 174),figfn,frame_name,frame_name))
    print("Annotating images")

    annotation_list.append([30,940,c_day.strftime("%a %d %b"),False])
    
    annotate_picture(frame_name,annotation_list)
        
#Generate plot
#plt.figure(figsize=(11,14),frameon=False)
 #f=plt.figure(figsize=(12,14),dpi=113.72,frameon=False) 
#plt.axis([133000,658000,10600,655000])
#plt.text(550000,595000,title_string, horizontalalignment='center',fontsize=26)
#Version 1.3: Added optional daily update to date string
# if(daily_update):
#     s_date = datetime(2020,2,4)
#     s_date += timedelta(days = ((7 * (week - 1)) + int( (7.0 * frame) / frames_per_week)))
#     date_string = s_date.strftime("%B %d") #Format date to [Month Day] eg September 22
#plt.text(550000,576000,date_string, horizontalalignment='center', style='italic',fontsize=15)
#plt.axis('off')
 
#Create filenames
#sfn = "frame%04d.png" % (frame_count)
#ofn = overlay_path + os.path.sep + sfn
#rfn = merged_path + os.path.sep + sfn
#Save the plot as transparent PNG (tight bounding box removes most of border)
#plt.savefig(ofn, bbox_inches='tight')
#Add the new outbreaks to the list of historical outbreaks for future frames
#historical_outbreaks.extend(frame_outbreaks)
#Call convert (from imagemagick package) to create composite of background and new image
#os.system('convert %s %s -composite +antialias %s' % (background_filename,ofn,rfn))
#Clear the figure
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