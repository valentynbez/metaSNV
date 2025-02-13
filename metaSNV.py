#!/usr/bin/env python
# This code is part of the metagenomic SNV calling pipeline (metaSNV)
# Helper script to initiate a new project file structure.
import argparse
from sys import stderr, exit
from os import path
from glob import glob
import os
import sys
import shutil
import subprocess
import multiprocessing

from metaSNV.utils import create_output_folder
from metaSNV.bam_preprocessing import BAMInfo, write_legacy
from multiprocessing import Pool


basedir = os.path.dirname(os.path.abspath(__file__))




def exit_worker(signum, frame):
    raise RuntimeError("Keyboard Interrupt")


def init_worker():
    import signal
    signal.signal(signal.SIGINT, exit_worker)


def run_sample(sample, command):
    '''Simply wraps subprocess.call and returns contextual information in order
    to provide a good error message (if necessary)'''

    ret = subprocess.call(command)
    return sample, command, ret


def execute_snp_call(args, snpCaller, ifile, ofile, bam_filepaths):
    db_ann_args = []
    if args.db_ann != '':
        db_ann_args = ['-g', args.db_ann]
    samtools_cmd = ['samtools',
                    'mpileup',
                    '-f', args.ref_db, '-B', *bam_filepaths]
    snpcaller_cmd = [
        snpCaller, '-f', args.ref_db] + db_ann_args + [
            '-i', ifile, '-c', str(args.min_pos_cov), '-t', str(args.min_pos_snvs)]
    if args.print_commands:
        print(" ".join(samtools_cmd + ['|'] + snpcaller_cmd + ['>', ofile]))
    else:
        with open(ofile, 'wt') as ofile:
            samtools_call = subprocess.Popen(samtools_cmd, stdout=subprocess.PIPE)
            snpcaller_call = subprocess.Popen(snpcaller_cmd, stdin=samtools_call.stdout, stdout=ofile)
            samtools_call.stdout.close()
            return snpcaller_call.wait()


def snp_call(args, bam_filepaths):
    out_dir = path.join(args.project_dir, 'snpCaller')
    os.makedirs(out_dir, exist_ok=True)

    snpCaller = basedir + "/metaSNV/snpCaller/snpCall"

    indiv_out = path.join(out_dir, "indiv_called")
    called_SNP = path.join(out_dir, "called_SNPs")


# # ACTUAL COMMANDLINE
#       Note: Due to a bug in samtools v0.1.18, -Q 20 might be erroneous to use.
#       Note: Different phred score scales might be disregarded.
#       Note: If samtools > v0.1.18 is used -Q 20 filtering is highly recommended.

    v = execute_snp_call(args, snpCaller, indiv_out, called_SNP, bam_filepaths)
    if v is not None:
        if v > 0:
            stderr.write("SNV calling failed")
            exit(1)


def main():
    parser = argparse.ArgumentParser(description='Compute SNV profiles')
    parser.add_argument('project_dir', metavar='DIR',
                        help='The output directory that metaSNV will create e.g. "outputs". Can be a path.')
    parser.add_argument('input_folder', metavar='INPUT_DIR',
                        help='File with an input list of bam files, one file per line')
    parser.add_argument("ref_db", metavar='REF_DB_FILE',
                        help='reference multi-sequence FASTA file used for the alignments.')
    parser.add_argument('--db_ann', metavar='DB_ANN_FILE', default='',
                        help='Database gene annotation.')
    parser.add_argument('--print-commands', default=False, action='store_true',
                        help='Instead of executing the commands, simply print them out')
    parser.add_argument('--threads', metavar='INT', default=1, type=int,
                        help=('Number of jobs to run simmultaneously. '
                              'Will create same number of splits, unless n_splits set differently.'))
    parser.add_argument('--n_splits', metavar='INT', default=1, type=int,
                        help='Number of bins to split ref into')
    parser.add_argument('--use_prev_cov', default=False, action="store_true",
                        help=('Use "cov/" and "outputs.all_cov.tab" and "outputs.all_perc.tab" '
                              'data produced by previous metaSNV run'))
    parser.add_argument('--min_pos_cov', metavar='INT', default=4, type=int,
                        help='minimum coverage (mapped reads) per position for snpCall.')
    parser.add_argument('--min_pos_snvs', metavar='INT', default=4, type=int,
                        help='minimum number of non-reference nucleotides per position for snpCall.')

    args = parser.parse_args()
    args.project_dir = args.project_dir.rstrip('/')
    if not path.isfile(args.ref_db):
        stderr.write('''
ERROR:	No reference database or annotation file found!"
ERROR:	'{}' is not a file."

SOLUTION: run getRefDB.sh or set up a custom database before running metaSNP caller
        '''.format(args.ref_db))
        parser.print_help()
        exit(1)

    if not path.isfile(basedir+"/metaSNV/snpCaller/snpCall"):
        stderr.write('''
ERROR:  No binaries found

SOLUTION: make\n\n''')
        exit(1)

    if not shutil.which("samtools"):
        stderr.write('''
ERROR:  Samtools is not installed or couldn't be found.

SOLUTION: Install samtools or add it to $PATH\n\n''')
        exit(1)

    if args.threads > 1 and args.n_splits == 1:
        args.n_splits = args.threads

    create_output_folder(args.project_dir)

    # if not args.use_prev_cov:
    #     compute_opt(args)
    #     compute_summary(args)

    # get_header(args)

    # alternative
    files = sorted([f for f in os.listdir(args.input_folder) if f.endswith('.bam')])
    bam_filepaths = [os.path.join(args.input_folder, f) for f in files]
    with Pool(args.threads) as p:
        results = p.map(BAMInfo.from_bam, bam_filepaths)

    results_dict = {bam_info.sample : bam_info for bam_info in results}
    # sort by key
    results_dict = {k: results_dict[k] for k in sorted(results_dict)}

    project_name = path.basename(args.project_dir)
    write_legacy(results_dict, "{}/{}.all_cov.tab".format(args.project_dir, project_name), "depth")
    write_legacy(results_dict, "{}/{}.all_perc.tab".format(args.project_dir, project_name), "breadth")

    snp_call(args, bam_filepaths)


if __name__ == '__main__':
    main()
