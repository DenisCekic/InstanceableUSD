import omni.usd
import omni.client
from pxr import Usd, Sdf, UsdGeom, UsdPhysics, PhysxSchema

def setup_visuals_and_collisions(asset_usd_path, source_prim_path, save_as_path=None):
    print(f"Opening stage: {asset_usd_path}")
    omni.usd.get_context().open_stage(asset_usd_path)
    stage = omni.usd.get_context().get_stage()

    prims = [stage.GetPrimAtPath(source_prim_path)]
    edits = Sdf.BatchNamespaceEdit()
    collision_containers = set()

    while prims:
        prim = prims.pop(0)
        type_name = prim.GetTypeName()

        if type_name in ["Mesh", "Capsule", "Sphere", "Box"]:
            mesh_path = prim.GetPath()
            parent_path = mesh_path.GetParentPath()
            mesh_name = mesh_path.name

            #/visuals scope 
            visuals_path = parent_path.AppendChild("visuals")
            if not stage.GetPrimAtPath(visuals_path).IsValid():
                visuals_prim = stage.DefinePrim(visuals_path)
                visuals_prim.SetInstanceable(True)
                print(f" - Created visuals: {visuals_path}")
            else:
                visuals_prim = stage.GetPrimAtPath(visuals_path)
                visuals_prim.SetInstanceable(True)

            #Reparent mesh to visuals/
            new_visual_path = visuals_path.AppendChild(mesh_name)
            print(f" - Moving {mesh_path} under {visuals_path}")
            edits.Add(Sdf.NamespaceEdit.Reparent(mesh_path, visuals_path, 0))

            #/collision scope 
            collision_path = parent_path.AppendChild("collision")
            collision_containers.add(collision_path)

            if not stage.GetPrimAtPath(collision_path).IsValid():
                collision_prim = stage.DefinePrim(collision_path)
                print(f" - Created collision: {collision_path}")

            new_collision_path = collision_path.AppendChild(mesh_name)
            if not stage.GetPrimAtPath(new_collision_path).IsValid():
                #Create proper geometry type
                if type_name == "Mesh":
                    collision_geom = UsdGeom.Mesh.Define(stage, new_collision_path)
                elif type_name == "Capsule":
                    collision_geom = UsdGeom.Capsule.Define(stage, new_collision_path)
                elif type_name == "Sphere":
                    collision_geom = UsdGeom.Sphere.Define(stage, new_collision_path)
                elif type_name == "Box":
                    collision_geom = UsdGeom.Cube.Define(stage, new_collision_path)
                else:
                    print(f" - Skipping unknown type: {type_name}")
                    continue

                collision_geom.GetPurposeAttr().Set("guide")
                print(f" - Duplicated to {new_collision_path} (guide)")

                #Copy geometry from original BEFORE move
                src_geom = UsdGeom.Mesh(prim)
                dst_geom = collision_geom

                if src_geom and dst_geom:
                    dst_geom.GetPointsAttr().Set(src_geom.GetPointsAttr().Get())
                    dst_geom.GetFaceVertexCountsAttr().Set(src_geom.GetFaceVertexCountsAttr().Get())
                    dst_geom.GetFaceVertexIndicesAttr().Set(src_geom.GetFaceVertexIndicesAttr().Get())
                    if src_geom.GetNormalsAttr().HasAuthoredValue():
                        dst_geom.GetNormalsAttr().Set(src_geom.GetNormalsAttr().Get())
                    print(f" - Geometry copied to: {dst_geom.GetPath()}")

        prims.extend(prim.GetChildren())

    #Apply all reparenting edits
    stage.GetRootLayer().Apply(edits)

    #Remove ALL physics APIs from everything 
    print("Stripping ALL physics APIs...")
    for prim in stage.Traverse():
        if prim.GetTypeName() not in ["Mesh", "Capsule", "Sphere", "Box"]:
            continue
        for api in [
            PhysxSchema.PhysxCollisionAPI,
            PhysxSchema.PhysxConvexHullCollisionAPI,
            PhysxSchema.PhysxConvexDecompositionCollisionAPI,
            UsdPhysics.CollisionAPI,
            UsdPhysics.MeshCollisionAPI,
            UsdPhysics.RigidBodyAPI
        ]:
            if api.CanApply(prim):
                api.Get(stage, prim.GetPath()).GetPrim().RemoveAPI(api)

    #Reapply full convex decomposition API stack to /collision meshes
    print("Applying convex decomposition to /collision meshes...")
    for prim in stage.Traverse():
        if prim.GetTypeName() not in ["Mesh", "Capsule", "Sphere", "Box"]:
            continue
        parent = prim.GetParent()
        if not parent or not str(parent.GetPath()).endswith("/collision"):
            continue

        UsdPhysics.CollisionAPI.Apply(prim)
        PhysxSchema.PhysxCollisionAPI.Apply(prim)
        PhysxSchema.PhysxConvexHullCollisionAPI.Apply(prim)
        UsdPhysics.MeshCollisionAPI.Apply(prim)
        PhysxSchema.PhysxConvexDecompositionCollisionAPI.Apply(prim)

        #Set USDA attribute for physics approximation ie. "convexDecomposition" , "sdf"
        prim.CreateAttribute("physics:approximation", Sdf.ValueTypeNames.Token, custom=False).Set(
            UsdPhysics.Tokens.convexDecomposition
        )

        print(f" - Convex Decomposition Collider applied: {prim.GetPath()}")

    #Mark /collision scope as instanceable 
    print("Marking /collision containers as instanceable...")
    for path in collision_containers:
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            prim.SetInstanceable(True)
            print(f" - Marked instanceable: {path}")

    #Save 
    if save_as_path is None:
        print("Saving to original file.")
        omni.usd.get_context().save_stage()
    else:
        print(f"Saving to new file: {save_as_path}")
        omni.usd.get_context().save_as_stage(save_as_path)

#Define paths and source prim of USD that gets converted to IsaacLab instanceable USD, if save_as_path is None, it will overwritte original USD
asset_usd_path = #"Path/to/original/usd/file.usd"
source_prim_path = #"/World/MainXform"
save_as_path = #None or "Path/to/Converted/usd/file.usd"

setup_visuals_and_collisions(asset_usd_path, source_prim_path, save_as_path)
