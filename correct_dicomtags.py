# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "argparse",
#     "pydicom",
# ]
# ///

import argparse as arg
import pydicom

COPY_DICOM_TAGS = {
    # important for grouping
    "PatientID",
    "PatientName",
    "PatientBirthDate",
    "StudyInstanceUID",

    # additional information
    "StudyID",
    "AcquisitionDate",
    "PatientSex",
    "MagneticFieldStrength",
    "Manufacturer",
    "ManufacturerModelName",
    "Modality",
    "StudyDescription",
    "InstitutionName",
}

IMAGE_COMMENTS = "*** NOT APPROVED FOR CLINICAL USE ***"
ACCESSION_NUMBER = "1"
INSTITUTION_NAME = "UZLEUVEN"



# dataset_template = pydicom.dcmread(args.template)
# dataset = pydicom.dcmread(path_to_output)

# # Copy tags from template (to guarantee grouping with original data)
# update_dicom_tags = {}
# for tag in COPY_DICOM_TAGS:
#     try:
#         update_dicom_tags[tag] = getattr(dataset_template, tag)
#     except:
#         update_dicom_tags[tag] = ""



# for tag in sorted(update_dicom_tags.keys()):
#     value = update_dicom_tags[tag]
#     setattr(dataset, tag, value)
#     ph.print_info("%s: '%s'" % (tag, value))

# dataset.save_as(path_to_output)

def correct_dicomtags(input: str,
                      output: str,
                      donor: str,
                      label: str,
                      seriesnumber: str,
                      ):
    donor_dicom = pydicom.dcmread(donor)
    input_dicom = pydicom.dcmread(input)

    # Copy tags from template (to guarantee grouping with original data)
    update_dicom_tags = {}
    for tag in COPY_DICOM_TAGS:
        try:
            update_dicom_tags[tag] = getattr(donor_dicom, tag)
        except:
            update_dicom_tags[tag] = ""

    # Additional tags
    update_dicom_tags["SeriesDescription"] = label
    # update_dicom_tags["InstitutionName"] = INSTITUTION_NAME
    update_dicom_tags["ImageComments"] = IMAGE_COMMENTS
    update_dicom_tags["AccessionNumber"] = ACCESSION_NUMBER
    update_dicom_tags["SeriesNumber"] = seriesnumber

    for tag in sorted(update_dicom_tags.keys()):
        value = update_dicom_tags[tag]
        setattr(input_dicom, tag, value)
        print("%s: '%s'" % (tag, value))

    input_dicom.save_as(output)
    print(f"3D DICOM image written to {output}.")
    

def main():
    parser = arg.ArgumentParser(
        prog='correct_dicomtags',
        description='Correct dicomtags of a given dicom file, based on a donor dicom.',
    )

    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-o', '--output', required=True)
    parser.add_argument('-d', '--donor', required=True)
    parser.add_argument('-l', '--label', required=True)
    parser.add_argument('-n', '--seriesnumber', required=True)
    
    args = parser.parse_args()

    correct_dicomtags(args.input,
                      args.output,
                      args.donor,
                      args.label,
                      args.seriesnumber)
    

if __name__ == "__main__":
    main()
