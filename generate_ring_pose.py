import bpy
import math
import os
from mathutils import Euler, Quaternion, Vector

def create_show_off_ring_animation():
    print("[ShowOffRing] Generating 2-second 'Show Off Ring' animation...")

    import addon_utils
    addon_utils.enable("bl_ext.blender_org.vrm")

    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    vrm_path = r"D:/AI-Automation/AI-Automation Frontend/public/avatar/Latest_Avatar.vrm"
    output_vrma = r"D:/AI-Automation/AI-Automation Frontend/public/avatar/animations/ShowOffRing.vrma"
    output_fbx = r"D:/AI-Automation/AI-Automation Frontend/public/avatar/animations/ShowOffRing.fbx"

    bpy.ops.import_scene.vrm(filepath=vrm_path)

    armature = None
    face_mesh = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE' and armature is None:
            armature = obj
        if obj.type == 'MESH' and 'face' in obj.name.lower():
            face_mesh = obj

    if not armature:
        raise RuntimeError("No Armature found after VRM import")

    print(f"[ShowOffRing] Found Armature: {armature.name}")

    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')

    FPS = 30
    TOTAL_FRAMES = 60  # 2.0 seconds at 30 FPS
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = TOTAL_FRAMES

    action = bpy.data.actions.new(name="Show_Off_Ring_2s")
    if not armature.animation_data:
        armature.animation_data_create()
    armature.animation_data.action = action

    pb = armature.pose.bones
    hips = pb.get('J_Bip_C_Hips')
    spine = pb.get('J_Bip_C_Spine')
    chest = pb.get('J_Bip_C_Chest')
    neck = pb.get('J_Bip_C_Neck')
    head = pb.get('J_Bip_C_Head')

    l_shoulder = pb.get('J_Bip_L_Shoulder')
    l_arm = pb.get('J_Bip_L_UpperArm')
    l_forearm = pb.get('J_Bip_L_LowerArm')
    l_hand = pb.get('J_Bip_L_Hand')

    r_shoulder = pb.get('J_Bip_R_Shoulder')
    r_arm = pb.get('J_Bip_R_UpperArm')
    r_forearm = pb.get('J_Bip_R_LowerArm')

    # Left Finger bones
    l_thumb = [pb.get(f'J_Bip_L_Thumb{i}') for i in (1, 2, 3)]
    l_index = [pb.get(f'J_Bip_L_Index{i}') for i in (1, 2, 3)]
    l_middle = [pb.get(f'J_Bip_L_Middle{i}') for i in (1, 2, 3)]
    l_ring = [pb.get(f'J_Bip_L_Ring{i}') for i in (1, 2, 3)]
    l_little = [pb.get(f'J_Bip_L_Little{i}') for i in (1, 2, 3)]

    def smoothstep(edge0, edge1, x):
        t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
        return t * t * (3.0 - 2.0 * t)

    # Base resting posture (relaxed arms down)
    rest_l_arm = Euler((math.radians(10), math.radians(0), math.radians(-68)), 'XYZ').to_quaternion()
    rest_r_arm = Euler((math.radians(10), math.radians(0), math.radians(68)), 'XYZ').to_quaternion()
    rest_l_fa = Euler((0, 0, math.radians(-16)), 'XYZ').to_quaternion()
    rest_r_fa = Euler((0, 0, math.radians(16)), 'XYZ').to_quaternion()
    rest_hand = Euler((0, 0, 0), 'XYZ').to_quaternion()

    # Showcase Target Posture:
    # Left hand brought up to upper chest / collarbone level (~0.35m in front of chest)
    # Palm facing torso / back of hand facing camera to display the ring!
    show_l_arm = Euler((math.radians(-32), math.radians(-15), math.radians(-35)), 'XYZ').to_quaternion()
    show_l_fa = Euler((math.radians(35), math.radians(-65), math.radians(-55)), 'XYZ').to_quaternion()
    show_l_hand = Euler((math.radians(10), math.radians(20), math.radians(-15)), 'XYZ').to_quaternion()

    # Animate frame by frame
    for frame in range(0, TOTAL_FRAMES + 1, 2):
        # Motion curve:
        # 0 - 24 (0s - 0.8s): Smooth raise into pose
        # 24 - 44 (0.8s - 1.46s): Proud hold & subtle wrist shimmer
        # 44 - 60 (1.46s - 2.0s): Smooth settle back to rest
        if frame <= 24:
            prog = smoothstep(0, 24, frame)
        elif frame <= 44:
            prog = 1.0
        else:
            prog = 1.0 - smoothstep(44, 60, frame)

        # Subtle shimmer / sparkle micro-rotation on the wrist during the hold (frames 24 to 44)
        shimmer = math.sin((frame / 20.0) * math.pi) * 0.08 if (20 <= frame <= 46) else 0.0

        # 1. Left Arm & Hand
        if l_arm:
            l_arm.rotation_mode = 'QUATERNION'
            l_arm.rotation_quaternion = rest_l_arm.slerp(show_l_arm, prog)
            l_arm.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if l_forearm:
            l_forearm.rotation_mode = 'QUATERNION'
            l_forearm.rotation_quaternion = rest_l_fa.slerp(show_l_fa, prog)
            l_forearm.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if l_hand:
            l_hand.rotation_mode = 'QUATERNION'
            shimmer_hand = Euler((math.radians(10 + shimmer * 10), math.radians(20 - shimmer * 8), math.radians(-15)), 'XYZ').to_quaternion()
            target_h = rest_hand.slerp(shimmer_hand, prog)
            l_hand.rotation_quaternion = target_h
            l_hand.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 2. Left Fingers:
        # Ring finger stays straight / prominently extended!
        # Thumb, Index, Middle, Little curl in gently to emphasize the ring finger!
        curl_quat = Euler((0, 0, math.radians(-45 * prog)), 'XYZ').to_quaternion()
        straight_quat = Euler((0, 0, math.radians(5 * prog)), 'XYZ').to_quaternion()
        thumb_curl = Euler((math.radians(15 * prog), 0, math.radians(-25 * prog)), 'XYZ').to_quaternion()

        for b in l_thumb:
            if b:
                b.rotation_mode = 'QUATERNION'
                b.rotation_quaternion = thumb_curl
                b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for b in l_index:
            if b:
                b.rotation_mode = 'QUATERNION'
                b.rotation_quaternion = curl_quat
                b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for b in l_middle:
            if b:
                b.rotation_mode = 'QUATERNION'
                b.rotation_quaternion = curl_quat
                b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for b in l_little:
            if b:
                b.rotation_mode = 'QUATERNION'
                b.rotation_quaternion = curl_quat
                b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Ring finger extends prominently with a proud lift!
        for b in l_ring:
            if b:
                b.rotation_mode = 'QUATERNION'
                b.rotation_quaternion = straight_quat
                b.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 3. Right Arm (Casual relaxed counter-balance)
        if r_arm:
            r_arm.rotation_mode = 'QUATERNION'
            r_arm.rotation_quaternion = rest_r_arm
            r_arm.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if r_forearm:
            r_forearm.rotation_mode = 'QUATERNION'
            r_forearm.rotation_quaternion = rest_r_fa
            r_forearm.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 4. Spine, Chest, Shoulders (Proud stance)
        if spine:
            spine.rotation_mode = 'QUATERNION'
            spine.rotation_quaternion = Euler((math.radians(-1.5 * prog), math.radians(2.0 * prog), 0), 'XYZ').to_quaternion()
            spine.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if chest:
            chest.rotation_mode = 'QUATERNION'
            chest.rotation_quaternion = Euler((math.radians(-2.5 * prog), math.radians(3.0 * prog), 0), 'XYZ').to_quaternion()
            chest.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if l_shoulder:
            l_shoulder.rotation_mode = 'QUATERNION'
            l_shoulder.rotation_quaternion = Euler((0, 0, math.radians(2.5 * prog)), 'XYZ').to_quaternion()
            l_shoulder.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 5. Head & Neck:
        # Glances admiringly at hand first (frame 15-28), then turns toward camera with proud smirk (frame 28-44)
        if head:
            head.rotation_mode = 'QUATERNION'
            if frame < 28:
                # Look towards left hand
                h_yaw = math.radians(8.0 * prog)
                h_pitch = math.radians(4.0 * prog)
                h_roll = math.radians(-3.0 * prog)
            else:
                # Tilt head proudly up toward user
                h_yaw = math.radians(-3.0 * prog)
                h_pitch = math.radians(-5.0 * prog)
                h_roll = math.radians(4.5 * prog)
            head.rotation_quaternion = Euler((h_pitch, h_yaw, h_roll), 'XYZ').to_quaternion()
            head.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if neck:
            neck.rotation_mode = 'QUATERNION'
            neck.rotation_quaternion = Euler((math.radians(-1.0 * prog), math.radians(1.5 * prog), 0), 'XYZ').to_quaternion()
            neck.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # 6. Face Mesh (Proud Smirk & Wink / Happy Eyes)
    if face_mesh and face_mesh.data.shape_keys:
        sk = face_mesh.data.shape_keys.key_blocks

        def insert_sk(name, f, val):
            k = sk.get(name)
            if k:
                k.value = float(val)
                k.keyframe_insert("value", frame=f)

        # Smug proud smile
        insert_sk('Fcl_ALL_Joy', 0, 0.0)
        insert_sk('Fcl_ALL_Joy', 15, 0.6)
        insert_sk('Fcl_ALL_Joy', 32, 0.85)  # Peak proud smile
        insert_sk('Fcl_ALL_Joy', 48, 0.5)
        insert_sk('Fcl_ALL_Joy', 60, 0.0)

        # Charming wink on right eye as she shows off the ring
        insert_sk('Fcl_EYE_Joy_R', 0, 0.0)
        insert_sk('Fcl_EYE_Joy_R', 28, 0.0)
        insert_sk('Fcl_EYE_Joy_R', 34, 0.85)  # Cute wink!
        insert_sk('Fcl_EYE_Joy_R', 42, 0.0)

    # 7. Bezier Smoothing
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'
    bpy.context.preferences.edit.keyframe_new_handle_type = 'AUTO_CLAMPED'

    # 8. Export VRMA
    print(f"[ShowOffRing] Exporting VRMA to: {output_vrma}")
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.export_scene.vrma(filepath=output_vrma, armature_object_name=armature.name)
        print(f"[ShowOffRing] VRMA export SUCCESS! File size: {os.path.getsize(output_vrma)} bytes")
    except Exception as e:
        print(f"[ShowOffRing] VRMA export error: {e}")

    # Export FBX
    print(f"[ShowOffRing] Exporting FBX to: {output_fbx}")
    bpy.ops.export_scene.fbx(
        filepath=output_fbx,
        check_existing=False,
        use_selection=True,
        object_types={'ARMATURE'},
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_step=1.0,
        add_leaf_bones=False
    )
    print(f"[ShowOffRing] FBX export SUCCESS! File size: {os.path.getsize(output_fbx)} bytes")

if __name__ == "__main__":
    create_show_off_ring_animation()
