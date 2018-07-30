#### To generate the patched rom from the binary files/release zip:
1. Copy the US Mario Kart 64 rom into the directory and name it "Mario Kart 64 (U) [!].z64". Note that your rom must be in z64 format.
2. Run CM_import_level.py
3. You should end up with MK64_Micro_Mountain.z64


#### To generate the binary files found in the release zip:
1. Open the blender file in Blender (I used v2.79).
2. Run the following python scripts:

   seg7_nodetree
  
   shadernodes
  
3. Run the "export" script to generate most of binary files.
4. Select the object "Path"
5. Enter edit mode
6. Select (only) the first vertex in that object
7. Run the "path export" script. This will take a little while.
8. You can now follow the directions above.
