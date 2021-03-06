####Windows Install Instructions####
___

Note: This has been tested with Win 7 (as that was my only test machine), there maybe other steps required for different windows configurations.

#####1) Need to install Python 2.7#####

Download installer here for 2.7.10:
https://www.python.org/downloads/release/python-2710/

```
#test your install and make sure python in PATH (see step 5 for PATH info)
python -V
```
* some systems may require an update to C++, [here](http://www.microsoft.com/en-us/download/details.aspx?id=44266)


#####2) Open up command line in administrator mode
* Search for 'cmd' from start menu, right click and Run as Administrator

Install Python dependencies:
```
pip install biopython natsort
```
* to use the heatmap function you will also need to install `pip install matplotlib numpy pandas`

#####3) Now download this repository

You can download the newest release here:
https://github.com/nextgenusfs/amptk/releases

* unzip and move the folder to a known directory, i.e. C:\Program Files\amptk

#####4) Download/Install USEARCH8 - get it [here](http://www.drive5.com/usearch/download.html)#####
* copy usearch8 exe file into amptk folder (C:\Program Files\amptk)
* change file name to usearch8 (right click and rename)


#####5) Add location of scripts to PATH variable#####
See a walkthrough [here](http://www.howtogeek.com/118594/how-to-edit-your-system-path-for-easy-command-line-access/)

Short instructions:
* Open System Control Panel (Start - Settings - Control Panel - System)
* Select Advanced tab
* Open Environmental Variables
* Edit System Variables, Path
* Add to end of string, ;C:\Program Files\amptk
* Now close window
You may need to restart the command prompt for the new settings to be loaded correctly.

#####6) Test Installation
Open command prompt, navigate to the `test_data` folder of amptk.

```
#test scripts on Ion PGM data
amptk.py ion -i ion.test.fastq -o ion
#run clustering
amptk.py cluster -i ion.demux.fq -o ion --uchime_ref ITS2 --mock BC_5
```
```
#test scripts on MiSeq data
amptk.py illumina -i illumina_test_data/
#run clustering
amptk.py cluster -i amptk.demux.fq -o miseq --uchime_ref ITS2 --mock spike
```

#####7) Adding .PY to PATHEXT (optional)

You can add the `.py` extension to your executable path by following this [walkthrough](http://stackoverflow.com/a/13023969/4386003)


