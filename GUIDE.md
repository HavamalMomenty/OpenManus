cd OpenManus
source .venv/bin/activate
python run_flow.py


How to run:
    1. All input should be put inside the config file
    2. The input dir, workspace dir, and output dir have the following function:
        1 Input dir:
            Contains file / folders that we want to READ from
        2 Workspace dir:
            The directory within which we generate a unique run-specific workspace.
            We copy ALL files / folders of the input dir to this run-specific workspace (named after the current time)
        3 Output dir:
            The directory within which we generate a unique run-specific output.
            We copy all GENERATED / NEW files and folders of the run-specific workspace dir into the output dir. 