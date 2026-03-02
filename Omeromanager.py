import csv
import shlex
import subprocess
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

from omero.gateway import BlitzGateway
import omero.model  
import ezomero as ez

# ---------- Connection ----------
def connect(hostname, username, password):
    conn = BlitzGateway(username, password, host=hostname, port=4064, secure=True)
    if not conn.connect():
        raise ConnectionError("Failed to connect to the OMERO server")
    conn.c.enableKeepAlive(60)
    return conn

def change_group(conn, group_id):
    conn.setGroupForSession(group_id)

# ---------- Create Project/Dataset ----------
def get_or_create_project(conn, name, description=""):
    for prj in conn.getObjects("Project", attributes={"name": name}):
        return prj
    pid = ez.post_project(conn, name, description=description or "")
    return conn.getObject("Project", pid)

def get_or_create_dataset(conn, name, description="", project_id=None):
    for ds in conn.getObjects("Dataset", attributes={"name": name}):
        return ds
    did = ez.post_dataset(conn, name, description=description or "", project_id=project_id)
    return conn.getObject("Dataset", did)

def link_dataset_to_project_if_needed(conn, project, dataset):
    try:
        # Check if the dataset is already linked to the project
        if any(d.getId() == dataset.getId() for d in project.listChildren()):
            return
    except Exception as e:
        print(f"Warning while checking links: {e}. Attempting to link anyway.")

    try:
        # Manually create a project-dataset link using OMERO API
        link = omero.model.ProjectDatasetLinkI()
        link.setParent(omero.model.ProjectI(project.getId(), False))
        link.setChild(omero.model.DatasetI(dataset.getId(), False))
        conn.getUpdateService().saveObject(link)
        print(f"Dataset '{dataset.getName()}' successfully linked to Project '{project.getName()}'")
    except Exception as e:
        print(f"Error linking dataset '{dataset.getName()}' to project '{project.getName()}': {e}")

# ---------- CSV Processing ----------
def process_csv(conn, csv_path):
    summary = []

    def is_int_string(s):
        return s.isdigit()

    def get_group_id(conn, group_str):
        if is_int_string(group_str):
            return int(group_str)
        for g in conn.getGroups():
            if g.getName() == group_str:
                return g.getId()
        raise ValueError(f"Group '{group_str}' not found")

    def get_project_by_id(conn, project_id):
        prj = conn.getObject("Project", int(project_id))
        if prj is None:
            raise ValueError(f"Project ID '{project_id}' not found")
        return prj

    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        sample = f.read(1024)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
            reader = csv.DictReader(f, dialect=dialect)
        except csv.Error:
            f.seek(0)
            reader = csv.DictReader(f, delimiter=',')

        print("Raw headers:", reader.fieldnames)
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]
        print("Normalized headers:", reader.fieldnames)

        current_group = None

        for row in reader:
            if 'groups' not in row:
                print("Error: 'groups' column not found in row")
                continue

            group_str = row['groups'].strip()
            group_id = get_group_id(conn, group_str)

            if current_group != group_id:
                change_group(conn, group_id)
                current_group = group_id
                summary.append(f"== Group {group_id} ==")

            project_str = row['project'].strip()
            if is_int_string(project_str):
                prj = get_project_by_id(conn, project_str)
            else:
                prj = get_or_create_project(conn, project_str)

            summary.append(f"Project: {prj.getName()} (ID={prj.getId()})")

            datasets_raw = row['dataset'].split(',')
            for ds_name in [d.strip() for d in datasets_raw if d.strip()]:
                ds = get_or_create_dataset(conn, ds_name, project_id=prj.getId())
                link_dataset_to_project_if_needed(conn, prj, ds)
                summary.append(f"  - Dataset: {ds.getName()} (ID={ds.getId()})")

            summary.append("")
    return "\n".join(summary)


# ---------- GUI ----------
def main():
    root = tk.Tk()
    root.withdraw()
    conn = None
    try:
        host = simpledialog.askstring("Host", "Host:", initialvalue="xxx") #put your inicial host
        user = simpledialog.askstring("Username", "Username:")
        pw = simpledialog.askstring("Password", "Password:", show="*")
        if not all([host, user, pw]):
            return

        conn = connect(host, user, pw)

        csv_path = filedialog.askopenfilename(
            title="Select the CSV file",
            filetypes=[("CSV/TSV files", "*.csv *.tsv *.txt"), ("All files", "*.*")]
        )
        if not csv_path:
            messagebox.showwarning("Cancelled", "No file was selected.")
            return

        result = process_csv(conn, csv_path)
        messagebox.showinfo("Process Completed", result)

    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
