=========================================
OMERO Group Project-Dataset CSV Manager
=========================================

Description:
------------
This script automates the structured creation and organization of Projects and 
Datasets inside an OMERO server using a CSV file as input.

For each row in the CSV file, the script:

1. Connects to the OMERO server.
2. Switches to the specified group (by ID or name).
3. Searches for an existing Project.
4. Creates the Project if it does not exist.
5. Searches for existing Datasets.
6. Creates missing Datasets.
7. Links each Dataset to its corresponding Project (if not already linked).

This allows batch organization of data structures across multiple OMERO groups 
in a safe and controlled way, avoiding duplication.

How It Works Internally:
------------------------
Connection:
- Uses BlitzGateway to establish a secure session.
- Enables keep-alive to maintain connection stability.
- Uses SERVICE_OPTS to enforce group context switching properly.

Group Handling:
- Reads the value from the `groups` column.
- Accepts either:
    • Numeric Group ID
    • Exact Group Name
- Resolves the correct group ID before switching context.
- Forces the OMERO session to operate strictly within that group.

Project Search Logic:
- If the `project` value is numeric → treated as Project ID.
- If it is text → searched by name inside the active group.
- If not found → created automatically using ezomero.

Dataset Search Logic:
- Datasets are searched by name within the active group.
- If multiple dataset names are provided (comma-separated), each is processed individually.
- Missing datasets are created automatically.
- Existing datasets are reused.

Link Validation:
- Before linking a Dataset to a Project, the script checks whether the link 
  already exists.
- If not linked, a ProjectDatasetLink object is created via the OMERO API.
- This prevents duplicate relationships.

Summary Output:
- Every action (group switch, project creation/retrieval, dataset creation/linking)
  is recorded.
- A full execution summary is displayed at the end of the process.

CSV File Format:
----------------
The CSV must contain the following columns:
- `groups`
- `project`
- `dataset`
An example of the CSV file is attached.

Important Notes:
----------------
- The script processes rows sequentially.
- If consecutive rows belong to the same group, the group context remains active.
- Objects are always created inside the currently active group.
- No images are uploaded — this script only creates organizational structure.

Requirements:
-------------
Python 3.8+

Required libraries:
- tkinter (usually included)
- csv (standard library)
- shlex (standard library)
- subprocess (standard library)
- omero-py
- ezomero

Installation:
-------------
pip install omero-py
pip install ezomero

If tkinter is missing (Linux systems):
sudo apt-get install python3-tk

Usage:
------
1. Run the script:
   python Omeromanager.py

2. Enter:
   - OMERO Host, Username and Password

3. Select your CSV file.

Author and contact:
-------
Developed by Daurys De Alba
daurysdealbaherra@gmail.com
DeAlbaD@si.edu 
