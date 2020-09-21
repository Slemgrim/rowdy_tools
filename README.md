# Rowdy Tools

Rowdy Tools are my little helpers to manage assets in my blender pipeline

## Installation
Install it like every other blender addon

## Features

### Backup

Creates a backup file with increasing version number. The backups will have the prefix _b[x] where x is the version number. 
The prefix can be changed in settings. 

### Promote

In my workflow I usually have a scene directory, an asset directory and an edit directory.

* asset (contains all production ready assets)
* edit (contains the files i work on)
* scene (contains all scenes for rendering and links to assets)

When I'm done editing an asset in the edit directory I **promote** it to a production asset by copying it to the assets directory. 
This also means i have to change all linked libraries to their corresponding production versions. 

This helps to keep the projects organized but is very time consuming on bigger projects. 

The **promote** button does exactly this. It first checks whether an asset resides within a edit (edit) directory, then it checks if there exists a production (assets) directory upstream.
If so, the file get's copied over to the production directory.
If the asset has linked libraries, the production folder must contain the same assets or the plugin will not execute the promotion. 

## Preferences

* **Production folder name**: the name of the folder where the production assets are stored
* **Edit folder name**: the name of the folder where the unfinished assets are stored
* **Search Depth**: number of directories to go up when searching for edit- and asset-directory
* **Backup postfix**: the postfix which get's prepended to a backed up file

