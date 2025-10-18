#!/bin/sh
'''exec' uv run --script --project "$(dirname -- "$(realpath -- "$0")")" "$0" "$@"
' '''

import subprocess
import os
import tempfile
import shutil
from typing import cast
import nibabel as nib
import normalize_nifti as norm
import correct_dicomtags as cordictags
import argparse as arg
from pathlib import Path

IMAGE_COMMENTS = "NOT FOR CLINICAL USE"
ACCESSION_NUMBER = "1"

## 1: Create a temp working dir

def tmp_dir() -> tempfile.TemporaryDirectory:
    tmpdir = tempfile.TemporaryDirectory(prefix='nii2dcm_')
    return tmpdir

## 2: Normalize the nifti image --> nifti_norm

def normalize_image(in_path: Path, tmpdir: Path) -> Path:
    in_img = cast(nib.Nifti1Image, nib.load(str(in_path.absolute())))
    temp_nifti_norm = tmpdir / 'normalize_temp.nii'
    norm.normalize_nifti(in_img, str(temp_nifti_norm))
    return Path(temp_nifti_norm)

## Convert nifti_norm to 2d_dicom using nifti2dicom (docker)
def nifti_to_2d_dicom(
    in_path: Path,
    out_path: Path,
    donor_dcm: Path,
    seriesdesc: str,
    seriesnum: str,
    accession_number: str = "1",
    institution_name: str = "UZLEUVEN",
) -> Path:
    """
    Converts a NIfTI image to a 2D DICOM series using a Dockerized nifti2dicom tool.

    Args:
        in_path: Path to input NIfTI file.
        out_path: Directory where DICOM files will be written.
        donor_dcm: Path to reference DICOM file.
        seriesdesc: DICOM SeriesDescription.
        seriesnum: DICOM SeriesNumber.
        accession_number: DICOM AccessionNumber (default '1').
        institution_name: DICOM InstitutionName (default 'UZLEUVEN').

    Returns:
        Path to the output directory containing 2D DICOM files.
    """

    with tempfile.TemporaryDirectory(prefix="nii2dcm_") as tmpdir:
        tmpdir = Path(tmpdir)
        tmpdir.mkdir(exist_ok=True)

        # Copy input and donor files into the temporary mount directory
        input_copy = tmpdir / in_path.name
        donor_copy = tmpdir / donor_dcm.name
        shutil.copy2(in_path, input_copy)
        shutil.copy2(donor_dcm, donor_copy)

        print(f"Mount directory: {tmpdir}")

        # Run the Dockerized conversion
        cmd = [
            "docker", "run", "--rm",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "--mount", f"type=bind,src={tmpdir},target=/mnt",
            "nifti2dicom_ubuntu:0.1",
            "nifti2dicom",
            "-i", f"/mnt/{in_path.name}",
            "-o", "/mnt/2d_dicom/",
            "-d", f"/mnt/{donor_dcm.name}",
            "--prefix", "",
            "--seriesdescription", seriesdesc,
            "--accessionnumber", accession_number,
            "--seriesnumber", seriesnum,
            "--institutionname", institution_name,
        ]

        print(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        # Copy generated DICOMs to output directory
        shutil.copytree(tmpdir, out_path, dirs_exist_ok=True)

        return out_path

## Convert 2d_dicom to 3d_dicom using medcon (docker)
def to_3d_dicom(in_dir: Path) -> Path:
    """
    Converts all 2D DICOM slices in a directory into a single 3D DICOM file
    using medcon inside a Docker container.

    Args:
        in_dir: Directory containing the input .dcm files.

    Returns:
        Path to the generated 3D DICOM file (medcon.dcm) inside `in_dir`.
    """
    in_dir = Path(in_dir).absolute()
    output_path = in_dir / "medcon.dcm"

    cmd = [
        "docker", "run", "--rm",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "--mount", f"type=bind,src={in_dir},target=/mnt",
        "nifti2dicom_ubuntu:0.1",
        "bash", "-c",
        "medcon -f /mnt/*.dcm -o /mnt/medcon.dcm -c dicom -stack3d -n -qc -w"
    ]

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    if not output_path.exists():
        raise FileNotFoundError(f"Expected output not found: {output_path}")

    return output_path


## Correct dicomtags using pydicom
def correct_dicomtags(input: Path,
                      output: Path,
                      donor: Path,
                      label: str,
                      seriesnumber: str,
                      ) -> int:
    cordictags.correct_dicomtags(str(input.absolute()),
                                 str(output.absolute()),
                                 str(donor.absolute()),
                                 label,
                                 seriesnumber,
                                 )
    return 0


def pipeline(
    input_path: Path,
    output_path: Path,
    donor_path: Path,
    label: str,
    series_number: str,
    normalize: bool
) -> int:
    """
    Full processing pipeline:
    1. Optionally normalizes a NIfTI image.
    2. Converts the NIfTI to 2D DICOM slices.
    3. Combines those slices into a 3D DICOM volume.
    4. Corrects DICOM tags using a donor DICOM file.

    Args:
        input_path: Path to the input NIfTI file.
        output_path: Path where the final corrected 3D DICOM will be saved.
        donor_path: Path to the donor DICOM used for metadata.
        label: DICOM series description or label.
        series_number: DICOM series number.
        normalize: Whether to normalize the input NIfTI before conversion.

    Returns:
        Path to the final corrected 3D DICOM file.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)
    donor_path = Path(donor_path)

    with tempfile.TemporaryDirectory(prefix="nii2dcm_") as tmpdir:
        tmpdir = Path(tmpdir)
        print(f"Working in temporary directory: {tmpdir}")

        # Step 1 — optional normalization
        if normalize:
            print("Normalizing NIfTI image to signed int16...")
            normalized_img = normalize_image(input_path, tmpdir)
        else:
            print("Skipping normalization.")
            normalized_img = input_path

        # Step 2 — convert to 2D DICOMs
        print("Converting NIfTI to 2D DICOM slices...")
        nifti_to_2d_dicom(
            normalized_img,
            tmpdir,
            donor_path,
            label,
            series_number,
        )

        # Step 3 — merge 2D DICOMs into 3D DICOM
        print("Stacking 2D DICOMs into 3D DICOM volume...")
        medcon_file = to_3d_dicom(tmpdir / "2d_dicom")

        # Step 4 — correct tags using donor DICOM
        print("Correcting DICOM metadata using donor file...")
        final_output = correct_dicomtags(
            medcon_file, output_path, donor_path, label, series_number
        )

    print(f"Pipeline complete. Final DICOM: {final_output}")
    return final_output


def main():
    parser = arg.ArgumentParser(
        prog='nii2dcm.py',
        description='Convert niti image to dicom based on a given donor image.'
    )
    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-o', '--output', required=True)
    parser.add_argument('-d', '--donor', required=True)
    parser.add_argument('-l', '--label', required=True)
    parser.add_argument('-n', '--seriesnumber', required=True)
    parser.add_argument('-x', '--no-normalize', required=False, dest='normalize', action='store_false')
    parser.set_defaults(normalize=True)

    args = parser.parse_args()

    return pipeline(args.input,
             args.output,
             args.donor,
             args.label,
             args.seriesnumber,
             args.normalize)

    
    
if __name__ == "__main__":
    main()
