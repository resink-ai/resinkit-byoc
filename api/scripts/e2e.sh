#!/bin/bash
# shellcheck disable=SC2155,SC2044

set -e

function print_usage() {
    echo "Usage: $0 [test_function_name] [param1=value1 param2=value2 ...]"
    echo "       $0 list <module_name>"
    echo "Runs a specific e2e test or all e2e tests if no test function is specified"
    echo "Example: $0 test_list_catalog_stores"
    echo "Example: $0 test_delete_paimon_catalog paimon_catalog_name=test_catalog_123"
    echo "Example: $0 list catalogstore"
}

function list_test_cases() {
    local module_name=$1
    local test_file="tests/e2e/test_${module_name}.py"

    if [ ! -f "$test_file" ]; then
        echo "Error: Test file $test_file not found"
        exit 1
    fi

    echo "--------------------------------------------------------------"
    echo "Test cases in $test_file:"
    echo "--------------------------------------------------------------"
    # Print the test cases in the file, each starting with a number
    grep -o "def test_[a-zA-Z0-9_]*" "$test_file" | sed 's/def //' | sed 's/^/ - /'
}

function find_and_run_test() {
    local test_function=$1
    shift # Remove the first argument (test function name)
    local found=false
    local env_vars=""

    # Process any additional x=y arguments and set environment variables
    for arg in "$@"; do
        if [[ $arg == *=* ]]; then
            local var_name=$(echo "$arg" | cut -d= -f1)
            local var_value=$(echo "$arg" | cut -d= -f2-)
            env_vars+="TEST_VAR_${var_name}=${var_value} "
        fi
    done

    # If no test function is specified, run all e2e tests
    if [ -z "$test_function" ]; then
        echo "Running all e2e tests..."
        pytest tests/e2e/
        return
    fi

    echo "Looking for test function: $test_function"
    if [ -n "$env_vars" ]; then
        echo "With environment variables: $env_vars"
    fi

    # Find all e2e test files
    for test_file in $(find tests/e2e -name "test_*.py"); do
        # Use grep to find test classes that contain the function
        class_names=$(grep -l "def $test_function" "$test_file" | xargs grep -o "class [A-Za-z0-9_]*" | sed 's/class //')

        if [ -n "$class_names" ]; then
            for class_name in $class_names; do
                # Verify the function exists in this class
                if grep -q "def $test_function" "$test_file"; then
                    echo ""
                    echo "📌 Found test function in $test_file, class $class_name"

                    if [ -n "$env_vars" ]; then
                        echo "🚀 Running: $env_vars pytest "$test_file::$class_name::$test_function" -v --capture=no --tb=short"
                        echo ""
                        env $env_vars pytest "$test_file::$class_name::$test_function" -v --capture=no --tb=short
                    else
                        echo "🚀 Running: pytest $test_file::$class_name::$test_function -v"
                        echo ""
                        pytest "$test_file::$class_name::$test_function" -v --capture=no --tb=short
                    fi

                    found=true
                    break 2 # Break out of both loops
                fi
            done
        fi
    done

    if [ "$found" = false ]; then
        echo "Error: Test function '$test_function' not found in any e2e test file"
        exit 1
    fi
}

# Check for help flag
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    print_usage
    exit 0
fi

# Check for list command
if [ "$1" = "list" ]; then
    if [ -z "$2" ]; then
        echo "Error: Missing module name"
        print_usage
        exit 1
    fi
    list_test_cases "$2"
    exit 0
fi

# Get the test function name
test_function="$1"
shift # Remove the first argument

# Run the specified test with any additional arguments
find_and_run_test "$test_function" "$@"
