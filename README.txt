===========================
3DJUUMP Infinite Migration
===========================

Version Migration: 3.3 ➝ 4.1  
Purpose: Dump and upload users, teams, projects, and assets for the 3DJUUMP Infinite platform.

Directory structure:
- ../migration script/
  - dumpdirectorydbmigration.py
  - uploaddirectorydbmigration.py
  - assetmigration/
        - assetmigration.py
        - conf.json.tpl
        - conf.json
- ../migration_dump/
      - users.json
	  - teams.json
	  - projects.json
      - assets/
          - project_xxxxxxx.json
          - project_xxxxxxx.json

----------------------------------------------------------
1. OVERVIEW
----------------------------------------------------------

This migration tool performs a two-part process:

1. **Dumping** data from the 3.3 database.
2. **Uploading** data into the 4.1 system.

The process is divided into two categories:
- Users, Teams, and Projects
- Assets

Each script relies on a configuration file (`conf.json`) generated from `conf.json.tpl`.

----------------------------------------------------------
2. DUMPING USERS, TEAMS, AND PROJECTS
----------------------------------------------------------

**Script**: `dumpdirectorydbmigration.py`  
**Output**: `../migration_dump/users.json`
			`../migration_dump/teams.json`
			`../migration_dump/projects.json`
			`../migration_dump/assets/prj_xxxxxxx.json`

**Steps**:
1. Configure `conf.json` using `conf.json.tpl` as the template.
2. Run the script:

python dumpdirectorydbmigration.py


This will generate a dump of all users, teams, projects and assets per project.

----------------------------------------------------------
3. UPLOADING USERS, TEAMS, AND PROJECTS
----------------------------------------------------------

**Script**: `uploaddirectorydbmigration.py`  
**Input**:  `../migration_dump/users.json`
			`../migration_dump/teams.json`
			`../migration_dump/projects.json`

**Steps**:
1. Ensure `conf.json` is correctly filled.
2. Run the script:

python uploaddirectorydbmigration.py


Projects must be uploaded **before** their corresponding assets.

----------------------------------------------------------
4. UPLOADING ASSETS
----------------------------------------------------------

**Script**: `assetmigration.py`  
**Input**: `../migration_dump/assets/prj_xxxxxxx.json`

**Steps**:
1. Prepare a correct `conf.json` from `conf.json.tpl` with asset-related configuration.
2. Run the script with `conf.json` passed as an argument:

python assetmigration.py conf.json


**Instructions**:
- Upload assets one project at a time using the appropriate tools or scripts.
- Ensure that the associated project is already present in the target system.

----------------------------------------------------------
4. UPLOADING ASSETS
----------------------------------------------------------

Assets must be uploaded **after** their corresponding projects have been successfully uploaded.

**Instructions**:
- Upload assets one project at a time using the appropriate tools or scripts.
- Ensure that the associated project is already present in the target system.

----------------------------------------------------------
5. NOTES
----------------------------------------------------------

- Always verify the contents of `conf.json` before running any script.
- Ensure you follow the correct order:  
  1. Dump users/teams/projects/assets
  2. Upload users/teams/projects  
  3. Upload assets (project-by-project)

- Migration output is saved in the `../migration_dump/` folder relative to the script directory.

----------------------------------------------------------
6. SUPPORT
----------------------------------------------------------

If you encounter issues with the migration process, verify:
- `conf.json` has all required fields.
- You are following the correct upload order.
- The asset upload is done only after its corresponding project is already uploaded.