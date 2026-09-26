import bpy
import math
import os
from mathutils import Euler, Quaternion, Vector

def create_custom_idle():
    print("[CustomIdle] Starting 8-second expressive emotion & speech animation generation...")

    # Enable VRM Add-on
    import addon_utils
    addon_utils.enable("bl_ext.blender_org.vrm")

    # Clear existing scene objects
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    vrm_path = r"D:/AI-Automation/AI-Automation Frontend/public/avatar/Latest_Avatar.vrm"
    output_vrma = r"D:/AI-Automation/AI-Automation Frontend/public/avatar/animations/CustomIdle8s.vrma"
    output_fbx = r"D:/AI-Automation/AI-Automation Frontend/public/avatar/animations/CustomIdle8s.fbx"

    # Import VRM Model
    print(f"[CustomIdle] Importing VRM from: {vrm_path}")
    bpy.ops.import_scene.vrm(filepath=vrm_path)

    # Find Armature and Face Mesh
    armature = None
    face_mesh = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE' and armature is None:
            armature = obj
        if obj.type == 'MESH' and 'face' in obj.name.lower():
            face_mesh = obj

    if not armature:
        raise RuntimeError("No Armature found after VRM import")

    print(f"[CustomIdle] Found Armature: {armature.name}, Face Mesh: {face_mesh.name if face_mesh else 'None'}")

    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')

    # Animation configuration: 8 seconds at 30 FPS = 240 frames
    FPS = 30
    TOTAL_FRAMES = 240
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = TOTAL_FRAMES

    action_name = "Custom_Idle_8s"
    action = bpy.data.actions.new(name=action_name)
    if not armature.animation_data:
        armature.animation_data_create()
    armature.animation_data.action = action

    # Identify Key Humanoid Bones
    pb = armature.pose.bones
    hips = pb.get('J_Bip_C_Hips')
    spine = pb.get('J_Bip_C_Spine')
    chest = pb.get('J_Bip_C_Chest')
    upper_chest = pb.get('J_Bip_C_UpperChest')
    neck = pb.get('J_Bip_C_Neck')
    head = pb.get('J_Bip_C_Head')

    l_shoulder = pb.get('J_Bip_L_Shoulder')
    r_shoulder = pb.get('J_Bip_R_Shoulder')
    l_arm = pb.get('J_Bip_L_UpperArm')
    r_arm = pb.get('J_Bip_R_UpperArm')
    l_forearm = pb.get('J_Bip_L_LowerArm')
    r_forearm = pb.get('J_Bip_R_LowerArm')

    initial_hip_loc = hips.location.copy() if hips else Vector((0, 0, 0))

    # Helper smoothstep curve (0 to 1)
    def smoothstep(edge0, edge1, x):
        t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
        return t * t * (3.0 - 2.0 * t)

    # Pose evaluation function for any given frame (0 to 240)
    # Guaranteed frame 0 == frame 240 for a seamless 8s loop
    for frame in range(0, TOTAL_FRAMES + 1, 3):
        # 4 Main Phases:
        # Phase 1: 0 to 60 (Sad)
        # Phase 2: 60 to 120 (Happy)
        # Phase 3: 120 to 180 (Angry & Pout)
        # Phase 4: 180 to 240 (Speaking "ah" & "eh" -> Smooth loop return)

        # Base weights for emotional posture blends
        # We ensure w_sad at frame 0 and frame 240 are mathematically equal
        if frame <= 60:
            # Entering/maintaining Sad (at frame 0, already in sad posture)
            w_sad = 0.75 + 0.25 * math.sin((frame / 60.0) * math.pi)
            w_happy = 0.0
            w_angry = 0.0
            w_speak = 0.0
        elif frame <= 120:
            # Transition Sad -> Happy
            blend = smoothstep(60, 80, frame)
            decay = smoothstep(105, 120, frame)
            w_sad = (1.0 - blend) * 0.75
            w_happy = blend * (1.0 - decay * 0.9)
            w_angry = 0.0
            w_speak = 0.0
        elif frame <= 180:
            # Transition Happy -> Angry & Pout
            blend = smoothstep(120, 138, frame)
            decay = smoothstep(168, 180, frame)
            w_sad = 0.0
            w_happy = 0.0
            w_angry = blend * (1.0 - decay)
            w_speak = 0.0
        else:
            # Frame 180 to 240: Speaking "ah" and "eh", then blending into Frame 0 Sad
            w_happy = 0.0
            w_angry = 0.0
            # Blend back to Sad in last 20 frames (220 to 240)
            loop_blend = smoothstep(224, 240, frame)
            w_sad = loop_blend * 0.75
            w_speak = (1.0 - loop_blend)

        # Continuous gentle breathing bob throughout
        breath_sin = math.sin((frame / 120.0) * 2 * math.pi)
        breath_factor = (1.0 - math.cos((frame / 60.0) * 2 * math.pi)) * 0.5

        # Speaking nod components
        # Word 1 "ah" peaks around frame 196
        ah_factor = math.exp(-((frame - 196) ** 2) / (2 * (6 ** 2)))
        # Word 2 "eh" peaks around frame 220
        eh_factor = math.exp(-((frame - 220) ** 2) / (2 * (6 ** 2)))

        # 1. Hips Motion
        if hips:
            hips.rotation_mode = 'QUATERNION'
            hip_yaw = math.radians(-1.5 * w_angry + 1.2 * w_happy)
            hip_roll = math.radians(1.2 * w_angry - 0.8 * w_happy)
            hip_pitch = math.radians(0.4 * breath_factor - 0.5 * w_sad)

            hips.rotation_quaternion = Euler((hip_pitch, hip_yaw, hip_roll), 'XYZ').to_quaternion()
            hips.location = Vector((
                initial_hip_loc.x + (0.015 * w_angry) - (0.012 * w_happy),
                initial_hip_loc.y + (0.003 * breath_factor) - (0.005 * w_sad),
                initial_hip_loc.z - (0.003 * w_sad) + (0.002 * w_happy)
            ))
            hips.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            hips.keyframe_insert(data_path="location", frame=frame)

        # 2. Spine & Chest (Emotional Posture)
        if spine:
            spine.rotation_mode = 'QUATERNION'
            # Sad = slump forward (+ pitch), Happy = upright (- pitch), Angry = stiff
            sp_pitch = math.radians(2.2 * w_sad - 1.5 * w_happy + 0.5 * w_angry + 0.3 * breath_sin)
            sp_yaw = math.radians(1.0 * w_angry - 0.8 * w_happy)
            sp_roll = math.radians(-0.8 * w_angry)
            spine.rotation_quaternion = Euler((sp_pitch, sp_yaw, sp_roll), 'XYZ').to_quaternion()
            spine.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if chest:
            chest.rotation_mode = 'QUATERNION'
            ch_pitch = math.radians(2.8 * w_sad - 2.6 * w_happy - 1.0 * w_angry + 0.8 * breath_sin)
            ch_yaw = math.radians(-1.2 * w_angry)
            ch_roll = math.radians(0.6 * w_happy)
            chest.rotation_quaternion = Euler((ch_pitch, ch_yaw, ch_roll), 'XYZ').to_quaternion()
            chest.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if upper_chest:
            upper_chest.rotation_mode = 'QUATERNION'
            uch_pitch = math.radians(1.5 * w_sad - 1.8 * w_happy - 0.8 * w_angry + 0.5 * breath_sin)
            upper_chest.rotation_quaternion = Euler((uch_pitch, 0, 0), 'XYZ').to_quaternion()
            upper_chest.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 3. Neck & Head (Expressive Head Angles + Speaking Nods)
        if neck:
            neck.rotation_mode = 'QUATERNION'
            nk_pitch = math.radians(3.5 * w_sad - 2.0 * w_happy + 1.0 * w_angry + 2.5 * ah_factor - 1.5 * eh_factor)
            nk_yaw = math.radians(-2.5 * w_angry + 1.5 * eh_factor)
            nk_roll = math.radians(1.2 * w_happy - 1.5 * eh_factor)
            neck.rotation_quaternion = Euler((nk_pitch, nk_yaw, nk_roll), 'XYZ').to_quaternion()
            neck.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if head:
            head.rotation_mode = 'QUATERNION'
            # Sad: head drops down (+ pitch). Happy: head tilts back & to side. Angry: indignant chin lift & turn.
            # Speaking "ah": emphatic nod down. Speaking "eh": inquisition head cock/tilt.
            hd_pitch = math.radians(5.0 * w_sad - 3.8 * w_happy - 2.5 * w_angry + 4.2 * ah_factor - 2.5 * eh_factor)
            hd_yaw = math.radians(-4.5 * w_angry + 2.0 * w_happy + 3.0 * eh_factor)
            hd_roll = math.radians(3.5 * w_happy - 2.5 * w_angry + 4.0 * eh_factor)
            head.rotation_quaternion = Euler((hd_pitch, hd_yaw, hd_roll), 'XYZ').to_quaternion()
            head.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 4. Shoulders (Sigh slump vs Proud lift vs Pout tension)
        if l_shoulder and r_shoulder:
            l_shoulder.rotation_mode = 'QUATERNION'
            r_shoulder.rotation_mode = 'QUATERNION'
            sh_lift = math.radians(-2.5 * w_sad + 2.2 * w_happy + 3.5 * w_angry + 0.6 * breath_sin)
            l_shoulder.rotation_quaternion = Euler((0, 0, sh_lift), 'XYZ').to_quaternion()
            r_shoulder.rotation_quaternion = Euler((0, 0, -sh_lift), 'XYZ').to_quaternion()
            l_shoulder.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            r_shoulder.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # 5. Arms & Forearms (Natural Resting -> Clenched Pout -> Expressive Relax)
        if l_arm and r_arm:
            l_arm.rotation_mode = 'QUATERNION'
            r_arm.rotation_mode = 'QUATERNION'
            # Pout posture: arms pull closer to the body; happy posture: arms relaxed
            arm_z = math.radians(-66 + 5.0 * w_angry - 3.0 * w_happy)
            l_arm.rotation_quaternion = Euler((math.radians(10 + 4.0 * w_sad), 0, arm_z), 'XYZ').to_quaternion()
            r_arm.rotation_quaternion = Euler((math.radians(10 + 4.0 * w_sad), 0, -arm_z), 'XYZ').to_quaternion()
            l_arm.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            r_arm.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if l_forearm and r_forearm:
            l_forearm.rotation_mode = 'QUATERNION'
            r_forearm.rotation_mode = 'QUATERNION'
            fa_z = math.radians(-16 - 6.0 * w_angry)
            l_forearm.rotation_quaternion = Euler((0, 0, fa_z), 'XYZ').to_quaternion()
            r_forearm.rotation_quaternion = Euler((0, 0, -fa_z), 'XYZ').to_quaternion()
            l_forearm.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            r_forearm.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # 6. Keyframe Facial Shape Keys in Blender
    if face_mesh and face_mesh.data.shape_keys:
        sk = face_mesh.data.shape_keys.key_blocks
        print(f"[CustomIdle] Keyframing facial shape keys: Sorrow, Joy, Angry, Pout, Mouth A (ah), Mouth E (eh)")

        def insert_sk(name, f, val):
            k = sk.get(name)
            if k:
                k.value = float(val)
                k.keyframe_insert("value", frame=f)

        # Zero out all target shape keys at boundary frames (0 and 240)
        target_keys = ['Fcl_ALL_Sorrow', 'Fcl_ALL_Joy', 'Fcl_ALL_Angry', 'Fcl_MTH_Small', 'Fcl_MTH_A', 'Fcl_MTH_E', 'Fcl_EYE_Close']
        for key_name in target_keys:
            if sk.get(key_name):
                sk.get(key_name).value = 0.0

        # --- Phase 1: SAD (0s - 2s / Frames 0 - 60) ---
        # Seamless loop: Starts in sad, peaks at frame 25, ramps down at 60
        insert_sk('Fcl_ALL_Sorrow', 0, 0.70)
        insert_sk('Fcl_ALL_Sorrow', 25, 0.85)
        insert_sk('Fcl_ALL_Sorrow', 55, 0.40)
        insert_sk('Fcl_ALL_Sorrow', 65, 0.00)

        # Sad blink
        insert_sk('Fcl_EYE_Close', 0, 0.0)
        insert_sk('Fcl_EYE_Close', 20, 0.0)
        insert_sk('Fcl_EYE_Close', 23, 0.95)
        insert_sk('Fcl_EYE_Close', 26, 0.0)

        # --- Phase 2: HAPPY (2s - 4s / Frames 60 - 120) ---
        insert_sk('Fcl_ALL_Joy', 60, 0.00)
        insert_sk('Fcl_ALL_Joy', 75, 0.75)
        insert_sk('Fcl_ALL_Joy', 95, 0.95)
        insert_sk('Fcl_ALL_Joy', 115, 0.40)
        insert_sk('Fcl_ALL_Joy', 125, 0.00)

        # Happy blink
        insert_sk('Fcl_EYE_Close', 90, 0.0)
        insert_sk('Fcl_EYE_Close', 93, 0.95)
        insert_sk('Fcl_EYE_Close', 96, 0.0)

        # --- Phase 3: ANGRY & POUTING (4s - 6s / Frames 120 - 180) ---
        insert_sk('Fcl_ALL_Angry', 120, 0.00)
        insert_sk('Fcl_ALL_Angry', 135, 0.80)
        insert_sk('Fcl_ALL_Angry', 155, 0.95)
        insert_sk('Fcl_ALL_Angry', 175, 0.35)
        insert_sk('Fcl_ALL_Angry', 182, 0.00)

        # Pouting mouth (Fcl_MTH_Small)
        insert_sk('Fcl_MTH_Small', 125, 0.00)
        insert_sk('Fcl_MTH_Small', 140, 0.70)
        insert_sk('Fcl_MTH_Small', 155, 0.90)
        insert_sk('Fcl_MTH_Small', 175, 0.30)
        insert_sk('Fcl_MTH_Small', 182, 0.00)

        # Angry blink
        insert_sk('Fcl_EYE_Close', 145, 0.0)
        insert_sk('Fcl_EYE_Close', 148, 0.95)
        insert_sk('Fcl_EYE_Close', 151, 0.0)

        # --- Phase 4: SPEECH "ah" and "eh" (6s - 8s / Frames 180 - 240) ---
        # Word 1: "ah" (Fcl_MTH_A)
        insert_sk('Fcl_MTH_A', 186, 0.00)
        insert_sk('Fcl_MTH_A', 196, 0.92)  # Peak wide "ah"
        insert_sk('Fcl_MTH_A', 206, 0.00)

        # Word 2: "eh" (Fcl_MTH_E)
        insert_sk('Fcl_MTH_E', 212, 0.00)
        insert_sk('Fcl_MTH_E', 222, 0.88)  # Peak wide "eh"
        insert_sk('Fcl_MTH_E', 232, 0.00)

        # Conversational blink before "eh"
        insert_sk('Fcl_EYE_Close', 208, 0.0)
        insert_sk('Fcl_EYE_Close', 211, 0.95)
        insert_sk('Fcl_EYE_Close', 214, 0.0)

        # Seamless Loop End: Returns to exact Frame 0 values at Frame 240
        insert_sk('Fcl_ALL_Sorrow', 230, 0.20)
        insert_sk('Fcl_ALL_Sorrow', 240, 0.70)  # Identical to frame 0 (0.70)
        insert_sk('Fcl_EYE_Close', 240, 0.0)
        insert_sk('Fcl_ALL_Joy', 240, 0.0)
        insert_sk('Fcl_ALL_Angry', 240, 0.0)
        insert_sk('Fcl_MTH_Small', 240, 0.0)
        insert_sk('Fcl_MTH_A', 240, 0.0)
        insert_sk('Fcl_MTH_E', 240, 0.0)

    # 7. Set Bezier Smoothing on All Curves
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'
    bpy.context.preferences.edit.keyframe_new_handle_type = 'AUTO_CLAMPED'

    curves_found = 0
    fcurves = getattr(action, "fcurves", None)
    if fcurves is not None:
        for fcurve in fcurves:
            curves_found += 1
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'BEZIER'
                kf.easing = 'AUTO'
    elif hasattr(action, "layers"):
        try:
            for layer in action.layers:
                for strip in layer.strips:
                    for channelbag in strip.channelbags:
                        for fcurve in channelbag.fcurves:
                            curves_found += 1
                            for kf in fcurve.keyframe_points:
                                kf.interpolation = 'BEZIER'
                                kf.easing = 'AUTO'
        except Exception as e:
            print(f"[CustomIdle] Note on curve interpolation traversal: {e}")

    print(f"[CustomIdle] Generated {curves_found} animation curves over {TOTAL_FRAMES} frames.")

    # 8. Export to VRMA using VRM Add-on
    print(f"[CustomIdle] Exporting VRMA to: {output_vrma}")
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.export_scene.vrma(filepath=output_vrma, armature_object_name=armature.name)
        print(f"[CustomIdle] VRMA export SUCCESS! File size: {os.path.getsize(output_vrma)} bytes")
    except Exception as e:
        print(f"[CustomIdle] VRMA export failed ({e}), falling back to FBX export...")

    # Also export FBX as standard cross-compatible asset
    print(f"[CustomIdle] Exporting FBX to: {output_fbx}")
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
    print(f"[CustomIdle] FBX export SUCCESS! File size: {os.path.getsize(output_fbx)} bytes")

if __name__ == "__main__":
    create_custom_idle()
