> [!NOTE]
**InstanceableUSD**
> 
Convert USD to Instanceable USD for IsaacLab robotics training:

This script prepares a standard USD asset for instanceable usage in IsaacLab, particularly for scenarios that require efficient replication of assets (e.g., multiple robot instances). It restructures the USD file by organizing geometry into visuals/ and collision/ scopes, strips all existing physics APIs, and re-applies the PhysX Convex Decomposition collision stack under the collision/ hierarchy.     



> [!IMPORTANT]
**Required Input Hierarchy**
 
Before using this script, the original USD file must be structured with each mesh prim nested under a parent Xform prim. This is crucial due to USD instancing limitations.     

To allow instancing while preserving transformation flexibility, each geometry must be placed under its own Xform that can be referenced in simulation environments.    



> [!WARNING]
**Invalid Structure (Will NOT work with instancing):**  
```none
/World     
    └── Robot     
          ├── Sphere      
          └── Box     
```

In this case, marking Collisions instanceable would fail because Sphere and Box do not sit under independent transforms.

**Corrected Structure (Required for instancing):**
```none
/World
  └── Robot
        ├── Sphere_Xform
        │     └── Sphere
        └── Box_Xform
              └── Box
```
Each geometry must be nested under its own Xform, which serves as the reference point during instancing.

> [!TIP]
**How to Use**
Update the following variables in the script:

asset_usd_path = "Path/to/original/file.usd"  
source_prim_path = "/World/MainXform"  
save_as_path = None or "Path/to/converted/file.usd"  #None will overwrite original usd file thats defined in asset_usd_path 

Then execute the script inside a Python-capable environment where Isaac Sim and IsaacLab are available (Omniverse Kit-compatible).
