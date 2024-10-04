from mbz_tools import compress_mbz_file, extract_mbz_file, tag_activities
import argparse

# read filenames from command line
parser = argparse.ArgumentParser(description='Read filenames from command line')
parser.add_argument('file', type=str, help='File to read')
args = parser.parse_args()
file_path = args.file

try:
    extract_mbz_file(file_path + ".mbz")
    tag_activities()
    compress_mbz_file(file_path)


except Exception as e:
    print(f'An error occurred: {e}')