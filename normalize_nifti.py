# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "argparse",
#     "nibabel",
#     "numpy",
# ]
# ///

import argparse as arg
import nibabel as nib
import numpy as np
from typing import TypeAlias, cast, Tuple


nifti1: TypeAlias = nib.Nifti1Image


def minmax_nifti(input: nifti1) -> Tuple[float, float]:
    max: float = np.max(input.get_fdata())
    min: float  = np.min(input.get_fdata())
    return min, max


def normalize_nifti(input: nifti1, output: str):
    min, max = minmax_nifti(input)
    a = 65534 / (max - min)
    b = 32767 - a * max
    out_nifti_data = input.get_fdata().copy()
    out_nifti_data *= a
    out_nifti_data += b
    out_nifti = nib.Nifti1Image(out_nifti_data,
                                input.affine,
                                input.header,
                                dtype=np.int16,
                                )
    nib.save(out_nifti, output)
    

def main():
    parser = arg.ArgumentParser(
        prog='normalize_nifti',
        description='Normalize the pixel values of a nifti file to conform to DICOM values (int16).',
    )

    parser.add_argument('-i', '--input', required=True, )
    parser.add_argument('-o', '--output', required=True, )
    args = parser.parse_args()
    input  = cast(nifti1, nib.load(args.input))
    
    normalize_nifti(input, args.output) 
    
if __name__ == "__main__":
    main()
