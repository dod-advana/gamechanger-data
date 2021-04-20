# this file is meant to be sourced into interactive bash terminal env

run_tests() (
  # this runs in subshell
  set -o nounset
  set -o errexit

  local venv_location="$1"
  local zip_file="$2"
  local test_module="$3"

  # unzip test package into tmp dir
  local temp_dir="$(mktemp -d)"
  unzip "$zip_file" -d "$temp_dir"
  local test_module_location=$(find "$temp_dir" -type d -name "$test_module")

  # run tests
  source "$venv_location"/bin/activate
  python -m unittest discover -v -b -s "$test_module_location" -p '*tests.py' || true

  # cleanup
  rm -r "$temp_dir"
)

# example usage
# run_tests /opt/gc-transformer-venv-green ./tests.zip cpu_ml_api_prereqs
