import subprocess
import os
import tempfile
import nibabel as nib
import normalize_nifti as norm
from pathlib import Path

IMAGE_COMMENTS = "NOT FOR CLINICAL USE"
ACCESSION_NUMBER = "1"

## 1: Create a temp working dir

def tmp_dir() -> tempfile.TemporaryDirectory:
    tmpdir = tempfile.TemporaryDirectory(prefix='nii2dcm_')
    return tmpdir

## 2: Normalize the nifti image --> nifti_norm

def normalize(in_path, tmpdir: tempfile.TemporaryDirectory) -> Path:
    in_img = nib.load(in_path)
    temp_nifti_norm = tempfile.TemporaryFile(suffix='.nii', prefix='normalize_', dir=tmpdir.name).name
    norm.normalize_nifti(in_img, temp_nifti_norm)
    return Path(temp_nifti_norm)

## Convert nifti_norm to 2d_dicom using nifti2dicom (docker)
def nifti_to_2d_dicom(in_path: str,
                      out_dir: str,
                      donor_dcm: str,
                      seriesdesc: str,
                      seriesnum: str) -> Path:
    nifti_file = Path(in_path)
    dcm_dir = nifti_file.parent / '2d_dicom'
    
    subprocess.run(['docker', 'run', '--mount', f"type=bind,src={dir},target=/mnt", 'nifti2dicom_ubuntu:0.1',
                    'nifti2dicom',
                    '-i', in_path,
                    '-o', dcm_dir.absolute(),
                    '-d', donor_dcm,
                    '--prefix', "''",
                    '--seriesdescription', seriesdesc,
                    '--accessionnumber', ACCESSION_NUMBER,
                    '--seriesnumber', seriesnum,
                    '--institutionname', IMAGE_COMMENTS,
                    '--manufacturersmodelname', 'UZLeuven',
                    '--protocolname', 'UZLeuven',
                    ])
    return dcm_dir


## Convert 2d_dicom to 3d_dicom using medcon (docker)
def 2d_to_3d_dicom(in_path, tmpdir: tempfile.tempfile.TemporaryDirectory)
