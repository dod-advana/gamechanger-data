import subprocess

# Define the S3 bucket name and prefix
prefix = "s3://advana-data-zone/bronze/gamechanger/pdf/"

# Build the AWS CLI command
aws_command = ["aws", "s3", "ls", f"s3://{prefix}"]

try:
    # Execute the AWS CLI command
    result = subprocess.run(aws_command, capture_output=True, text=True, check=True, shell=True)
    
    # Print the command output
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f"Error: {e.returncode}\n{e.stderr}")
