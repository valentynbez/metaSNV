import os

def create_output_folder(basedir):
    os.makedirs(basedir, exist_ok=True)
    for sub in ['cov',
                'bestsplits',
                'snpCaller',
                'filtered',
                'filtered/pop',
                'filtered/ind',
                'distances']:
        os.makedirs(os.path.join(basedir, sub), exist_ok=True)