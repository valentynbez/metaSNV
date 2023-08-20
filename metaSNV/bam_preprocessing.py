import os
import pysam
from pysam.libcalignmentfile import AlignmentFile

from typing import List, Dict

def mean(lst):
    return sum(lst) / len(lst)

def median(lst):
    lst = sorted(lst)
    if len(lst) % 2 == 0:
        return (lst[len(lst) // 2] + lst[len(lst) // 2 - 1]) / 2
    else:
        return lst[len(lst) // 2]


class BAMReference:

    def __init__(self, sample : str, ref_name: str, length: str):
        self.sample = sample
        self.ref_name = ref_name
        self.length = length
        self.pos2cov = {}

    def __repr__(self):
        return f"BAMReference('sample={self.sample}; reference={self.ref_name}')"

    def __str__(self):
        return f"AlignmentReference('sample={self.sample}; reference={self.ref_name}')"

    def add_coverage(self, pos, cov):
        self.pos2cov[pos] = cov

    def positions(self):
        return list(self.pos2cov.keys())

    def coverage_depth(self, mode):
        coverage = list(self.pos2cov.values())

        if mode == 'mean':
            return mean(coverage)
        elif mode == 'median':
            return median(coverage)
        elif mode == 'raw':
            return coverage
        else:
            raise ValueError(f"'{mode}' not supported")

    def coverage_breadth(self, depth=1):
        covered_bases = self.coverage_depth('raw')
        bases_over_thresh = [cov for cov in covered_bases if cov >= depth]
        breadth = len(bases_over_thresh) / self.length
        return breadth



class BAMInfo:

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.sample = os.path.basename(filepath).rsplit('.', 1)[0]
        self.references = {}

    def __repr__(self):
        return f"BAMInfo('sample={self.sample}')"

    def __str__(self) -> str:
        return f"BAMInfo('sample={self.sample}')"

    def __getitem__(self, ref):
        return self.references[ref]

    @classmethod
    def from_bam(cls, filepath: str):
        # silence pysam warning
        save = pysam.set_verbosity(0)
        # read file
        bam = AlignmentFile(filepath, 'rb')
        pysam.set_verbosity(save)

        info = cls(filepath)
        for ref, length in zip(bam.references, bam.lengths):
            info.references[ref] = BAMReference(info.sample, ref, length)
        bam.close()


        for line in pysam.depth("-a", filepath).split('\n'):
            if line:
                ref, pos, cov = line.split('\t')
                info.references[ref].add_coverage(int(pos), int(cov))

        return info

    def get_reference_names(self):
        return list(self.references.keys())




def write_legacy(data: Dict[str, BAMInfo], output_filepath: str, mode = "depth"):
    """
    Write legacy coverage files for backwards compatibility.

    Args:
        data (dict): dictionary of BAMInfo objects.
        output_dir (str): path to output directory.
    """

    ## DATA WRANGLING

    # get all filenames
    filenames = list(data.keys())
    # references - extract all possible references
    references = set()
    for bam_file_info in data.values():
        references.update(bam_file_info.references)

    # sort references
    all_references = sorted(list(references))

    # create rows of data with reference as first column
    rows = []
    # for each reference
    # get average coverage from each sample
    # and write it to file
    for ref in all_references:
        row = [ref]
        for sample_reference in data.values():
            if ref in all_references:
                # extract value for the reference
                if mode == "depth":
                    value = str(sample_reference[ref].coverage_depth('mean'))
                elif mode == "breadth":
                    value = str(sample_reference[ref].coverage_breadth(depth=1))
                # add it to the row
                row.append(value)
            else:
                raise ValueError(f"Reference '{ref}' not found in {bam_file_info.sample}\n"
                                 "Are all BAM files aligned to the same reference?")
        rows.append(row)


    with open(output_filepath, 'w') as f:
        f.write('\t')
        f.write('\t'.join(filenames) + '\n')

        if mode == "depth":
            header = ["TaxId"] + ["Average_cov"] * len(filenames)
        elif mode == "breadth":
            header = ["TaxId"] + ["Percentage_1x"] * len(filenames)
        f.write('\t'.join(header) + '\n')

        for row in rows:
            f.write('\t'.join(row) + '\n')