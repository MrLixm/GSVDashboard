# ![SuperTool](https://img.shields.io/badge/type-SuperTool-blueviolet) GSV Dashboard (GSVDB)

Preview and edit the Graph State Variables (GSV) at the current point in your
nodegraph (or anywhere). List local and global GSVs.

![demo](./demo.gif)


## Features

- Local and Global GSVs listing.
- Scene parsing modes for GSV listing :
  - logical_upsteam
  - upstream
  - all scene
- GSV values *used in parsed scene* listing
- Non-already-edited GSV can be edited using the values found.
- Listing of node using X selected GSV. (can be selected)

## Installation

Put the parent `GSVDashboard` into the `SuperTools` directory of a
location registered by the `KATANA_RESOURCES` env variable.

```batch
:: D:/myShelf/SuperTools/GSVDashboard/...
"ROOT=D:/myShelf"
"KATANA_RESOURCES=%ROOT%"
```

## Licensing 

**Apache License, Version 2.0** (OpenSource)

See [LICENSE.md](./LICENSE.md).

Here is a quick resume :

- ✅ The licensed material and derivatives may be used for commercial purposes.
- ✅ The licensed material may be distributed.
- ✅ The licensed material may be modified.
- ✅ The licensed material may be used and modified in private.
- ✅ This license provides an express grant of patent rights from contributors.
- 📏 A copy of the license and copyright notice must be included with the licensed material.
- 📏 Changes made to the licensed material must be documented

## TODO

- Add option to support parsing settings configuration in-scene.