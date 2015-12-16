#!/usr/bin/env python

import sys, os, re, gzip, subprocess, argparse, inspect, logging, csv, shutil
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import lib.ufitslib as ufitslib
from Bio.SeqIO.QualityIO import FastqGeneralIterator

class MyFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def __init__(self,prog):
        super(MyFormatter,self).__init__(prog,max_help_position=48)
class col:
    GRN = '\033[92m'
    END = '\033[0m'
    WARN = '\033[93m'

parser=argparse.ArgumentParser(prog='ufits-fastq2sra.py', usage="%(prog)s [options] -i folder",
    description='''Script to split FASTQ file from Ion, 454, or Illumina2 by barcode sequence into separate files for submission to SRA.  This script can take the BioSample worksheet from NCBI and create an SRA metadata file for submission.''',
    epilog="""Written by Jon Palmer (2015) nextgenusfs@gmail.com""",
    formatter_class=MyFormatter)

parser.add_argument('-i','--input', dest='FASTQ', required=True, help='Input FASTQ file or folder')
parser.add_argument('-o','--out', dest='out', default="sra", help='Basename for output folder/files')
parser.add_argument('--min_len', default=50, type=int, help='Minimum length of read to keep')
parser.add_argument('-b','--barcode_fasta', dest='barcodes', help='Multi-fasta file containing barcodes used')
parser.add_argument('-s','--biosample', dest='biosample', help='BioSample file from NCBI')
parser.add_argument('-p','--platform', dest='platform', default='ion', choices=['ion', 'illumina', '454', 'illumina2'], help='Sequencing platform')
parser.add_argument('-f','--fwd_primer', dest="F_primer", default='fITS7', help='Forward Primer (fITS7)')
parser.add_argument('-r','--rev_primer', dest="R_primer", default='ITS4', help='Reverse Primer (ITS4)')
parser.add_argument('-n', '--names', action='store_true', help='CSV mapping file BC,NewName')
parser.add_argument('--force', action='store_true', help='Overwrite existing directory')
args=parser.parse_args()


#check if name is in primer_db, else use input value
if args.F_primer in ufitslib.primer_db:
    FwdPrimer = ufitslib.primer_db.get(args.F_primer)
else:
    FwdPrimer = args.F_primer

#check if name is in primer_db, else use input value
if args.R_primer in ufitslib.primer_db:
    RevPrimer = ufitslib.primer_db.get(args.R_primer)
else:
    RevPrimer = args.R_primer

#add the linker for ion primers
if args.platform == 'ion':
    FwdPrimer = 'A' + FwdPrimer

def FindBarcode(Seq):
    global Barcodes
    for BarcodeLabel in Barcodes.keys():
        Barcode = Barcodes[BarcodeLabel]
        if Seq.startswith(Barcode):
            return Barcode, BarcodeLabel
    return "", ""

log_name = args.out + '.ufits.log'
if os.path.isfile(log_name):
    os.remove(log_name)

ufitslib.setupLogging(log_name)
FNULL = open(os.devnull, 'w')
cmd_args = " ".join(sys.argv)+'\n'
ufitslib.log.debug(cmd_args)
print "-------------------------------------------------------"

if args.platform != 'illumina' and not args.barcodes:
    ufitslib.log.error("For ion, 454, or illumina2 datasets you must specificy a multi-fasta file containing barcodes with -b or --barcode_fasta")
    os._exit(1)

#initialize script, log system info and usearch version
ufitslib.log.info("Operating system: %s" % sys.platform)

#count FASTQ records in input
ufitslib.log.info("Loading FASTQ Records")
total = ufitslib.countfastq(args.FASTQ)
size = ufitslib.checkfastqsize(args.FASTQ)
readablesize = ufitslib.convertSize(size)
ufitslib.log.info('{0:,}'.format(total) + ' reads (' + readablesize + ')')

#if --names given, load into dictonary
if args.names:
    with open(args.names, 'rU') as input:
            reader = csv.reader(input)
            namesDict = {col[0]:col[1] for col in reader}
else:
    ufitslib.log.info("No names csv passed, using BC header names")

#load barcode fasta file into dictonary
Barcodes = {}
files = []
with open(args.barcodes, 'rU') as input:
    for line in input:
        if line.startswith('>'):
            if args.names:
                name = namesDict(line[1:-1])
                name = name + ".fastq"          
            else:
                name = line[1:-1] + ".fastq"
            files.append(os.path.join(args.out,name))
            continue
        Barcodes[name]=line.strip()

#create directory and files for each barcode
if not os.path.exists(args.out):
    os.makedirs(args.out)
else:
    if not args.force:
        ufitslib.log.error("Directory %s exists, add --force argument to overwrite" % args.out)
        os._exit(1)
    else:
        shutil.rmtree(args.out)
        os.makedirs(args.out)

#ensure file names are unique        
files = set(files)

#this way will loop through the FASTQ file many times....not really what I want but it will work...
runningTotal = 0
for f in files:   
    with open(f, 'w') as output:
        ufitslib.log.info("working on %s" % (output.name))
        with open(args.FASTQ, 'rU') as input:
            for title, seq, qual in FastqGeneralIterator(input):
                Barcode, BarcodeLabel = FindBarcode(seq)
                if Barcode == "": #if not found, move onto next record
                    continue
                BarcodeLength = len(Barcode)
                seq = seq[BarcodeLength:]
                qual = qual[BarcodeLength:]
                if len(seq) < args.min_len: #filter out sequences less than 50 bp.
                    continue
                if BarcodeLabel in output.name:
                    output.write("@%s\n%s\n+\n%s\n" % (title, seq, qual))
    Count = ufitslib.countfastq(f)
    ufitslib.log.info('{0:,}'.format(Count) + ' reads contained valid barcodes')
    runningTotal += Count

ufitslib.log.info('{0:,}'.format(runningTotal) + ' total reads for sra submission')

ufitslib.log.info("Now Gzipping files")
gzip_list = []
for file in os.listdir(args.out):
    if file.endswith(".fastq"):
        gzip_list.append(file)

for file in gzip_list:
    file_path = os.path.join(args.out, file)
    new_path = file_path + '.gz'
    with open(file_path, 'rU') as orig_file:
        with gzip.open(new_path, 'w') as zipped_file:
            zipped_file.writelines(orig_file)
    os.remove(file_path)

mdlist = []
for file in os.listdir(args.out):
    if file.endswith(".fastq.gz"):
        mdlist.append(file)

#check for BioSample meta file
if args.biosample:
    ufitslib.log.info("NCBI BioSample file detected, creating SRA metadata file") 
    #load in BioSample file to dictionary
    with open(args.biosample, 'rU') as input:
        reader = csv.reader(input, delimiter='\t')
        BioDict = {col[1]:(col[0],col[-1],col[2]) for col in reader}

    #set some defaults based on the platform
    if args.platform == 'ion':
        header = 'bioproject_accession\tsample_name\tlibrary_ID\ttitle\tlibrary_strategy\tlibrary_source\tlibrary_selection\tlibrary_layout\tplatform\tinstrument_model\tdesign_description\tfiletype\tfilename\tbarcode\tforward_primer\treverse_primer\n'
        sequencer = 'ION_TORRENT'
        model = 'Ion Torrent PGM' 
        lib_layout = 'single'
    elif args.platform == '454':
        header = 'bioproject_accession\tsample_name\tlibrary_ID\ttitle\tlibrary_strategy\tlibrary_source\tlibrary_selection\tlibrary_layout\tplatform\tinstrument_model\tdesign_description\tfiletype\tfilename\tbarcode\tforward_primer\treverse_primer\n'
        sequencer = '_LS454'
        model = '454 GS FLX Titanium'
        lib_layout = 'single'
    elif args.platform == 'illumina':
        header = 'bioproject_accession\tsample_name\tlibrary_ID\ttitle\tlibrary_strategy\tlibrary_source\tlibrary_selection\tlibrary_layout\tplatform\tinstrument_model\tdesign_description\tfiletype\tfilename\tfilename2\tbarcode\tforward_primer\treverse_primer\n'
        sequencer = 'ILLUMINA'
        model = 'Illumina MiSeq'
        lib_layout = 'paired'
    else:
        ufitslib.log.error("You specified a platform that is not supported")
        os._exit(1)
    lib_strategy = 'AMPLICON'
    lib_source = 'GENOMIC'
    lib_selection = 'RANDOM PCR'
    filetype = 'fastq'
    
    #now open file for writing, input header and then loop through samples
    sub_out = args.out + '.submission.txt'
    with open(sub_out, 'w') as output:
        output.write(header)
        for file in mdlist:
            name = file.split(".fastq")[0]
            bioproject = BioDict.get(name)[1]
            bioproject = 'PRJNA'+bioproject
            sample_name = BioDict.get(name)[0]
            title = 'Fungal ITS amplicon sequencing of %s: sample %s' % (BioDict.get(name)[2], name)
            bc_name = file.split(".gz")[0]
            barcode_seq = Barcodes.get(bc_name)
            description = 'Fungal ITS amplicon library was created using a barcoded fusion primer PCR protocol using Pfx50 polymerase (Thermo Fisher Scientific), size selected, and sequenced on the %s platform.  Sequence data was minimally processed, sequences were exported directly from the sequencing platform and only the barcode (index sequence) was trimmed prior to SRA submission.' % (model)
            if args.platform == 'ion' or args.platform == '454':
                line = [bioproject,sample_name,name,title,lib_strategy,lib_source,lib_selection,lib_layout,sequencer,model,description,filetype,file,barcode_seq,FwdPrimer,RevPrimer]
            elif args.platform == 'illumina':
                line = [bioproject,sample_name,name,title,lib_strategy,lib_source,lib_selection,lib_layout,sequencer,model,description,filetype,file,file2,barcode_seq,FwdPrimer,RevPrimer]
            output.write('\t'.join(line)+'\n')

        
