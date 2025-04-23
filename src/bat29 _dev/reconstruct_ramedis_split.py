from datasets import load_dataset
import os
import json

data_dir = "../../data/tests/treatment/ramedis"   # Define the data directory


dataset_name = "RAMEDIS"
ramedis_test = load_dataset('chenxz/RareBench', dataset_name, split="test", trust_remote_code=True)
ramedis_test_list = [example for example in ramedis_test][:200]

print(len(ramedis_test_list))
input()
# Define the output file path
output_filename = "ramedis_test.jsonl"
output_filepath = os.path.join(data_dir, output_filename)

# Save the list to a JSONL file
with open(output_filepath, 'w', encoding='utf-8') as f_out:
    for example in ramedis_test_list:
        json_line = json.dumps(example)
        f_out.write(json_line + '\n')