# Replace 'input.txt' with the name of your input file
input_file = 'valami.txt'
output_file = 'output.txt'

with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
        # Strip newline and leading/trailing whitespace, split and join with '-'
        words = line.strip().split()
        new_line = '-'.join(words)
        outfile.write(new_line + '\n')

print(f"Converted lines saved to '{output_file}'")
