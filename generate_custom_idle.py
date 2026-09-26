import bpy
import math
import os
from mathutils import Euler, Quaternion, Vector

def create_custom_idle():
    print("[CustomIdle] Starting 8-second custom idle animation generation...")

    # Enable VRM Add-on
    import addon_utils
    addon_utils.enable("bl_ext.blender_org.vrm")

    # Clear existing scene objects without resetting addon registrations
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
    l_hand = pb.get('J_Bip_L_Hand')
    r_hand = pb.get('J_Bip_R_Hand')

    # Base resting posture (relaxed human arms, not T-pose)
    base_pose = {
        l_arm: Euler((math.radians(10), math.radians(0), math.radians(-68)), 'XYZ').to_quaternion() if l_arm else None,
        r_arm: Euler((math.radians(10), math.radians(0), math.radians(68)), 'XYZ').to_quaternion() if r_arm else None,
        l_forearm: Euler((math.radians(0), math.radians(0), math.radians(-16)), 'XYZ').to_quaternion() if l_forearm else None,
        r_forearm: Euler((math.radians(0), math.radians(0), math.radians(16)), 'XYZ').to_quaternion() if r_forearm else None,
    }

    initial_hip_loc = hips.location.copy() if hips else Vector((0, 0, 0))

    # Animate every 5 frames for clean Bezier sampling
    for frame in range(0, TOTAL_FRAMES + 1, 5):
        # 1. Breathing Cycle: 2 full breaths in 8 seconds (Period = 120 frames)
        breath_theta = (frame / 120.0) * (2 * math.pi)
        breath_factor = (1.0 - math.cos(breath_theta)) * 0.5  # Exactly 0 at frame 0, 120, 240

        # 2. Subtle Weight Shift: 1 full cycle in 8 seconds (Period = 240 frames)
        shift_theta = (frame / TOTAL_FRAMES) * (2 * math.pi)
        shift_sin = math.sin(shift_theta)                     # Exactly 0 at frame 0, 240
        shift_cos_factor = (1.0 - math.cos(2 * shift_theta)) * 0.5

        # Apply Hips (Lateral shift + subtle vertical breathing bob)
        if hips:
            hips.rotation_mode = 'QUATERNION'
            hip_euler = Euler((
                math.radians(0.4) * breath_factor,
                math.radians(0.8) * shift_sin,  # Yaw
                math.radians(0.6) * shift_sin   # Roll tilt
            ), 'XYZ')
            hips.rotation_quaternion = hip_euler.to_quaternion()
            hips.location = Vector((
                initial_hip_loc.x + (0.012 * shift_sin),
                initial_hip_loc.y + (0.003 * breath_factor),
                initial_hip_loc.z - (0.002 * shift_cos_factor)
            ))
            hips.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            hips.keyframe_insert(data_path="location", frame=frame)

        # Apply Spine (Harmonic compensation)
        if spine:
            spine.rotation_mode = 'QUATERNION'
            spine_euler = Euler((
                math.radians(0.5) * breath_factor,
                math.radians(-0.4) * shift_sin,
                math.radians(-0.3) * shift_sin
            ), 'XYZ')
            spine.rotation_quaternion = spine_euler.to_quaternion()
            spine.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Apply Chest & Upper Chest (Natural respiration expansion)
        if chest:
            chest.rotation_mode = 'QUATERNION'
            chest_euler = Euler((
                math.radians(1.2) * breath_factor,
                math.radians(-0.3) * shift_sin,
                math.radians(-0.3) * shift_sin
            ), 'XYZ')
            chest.rotation_quaternion = chest_euler.to_quaternion()
            chest.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if upper_chest:
            upper_chest.rotation_mode = 'QUATERNION'
            upper_chest_euler = Euler((
                math.radians(0.7) * breath_factor,
                0,
                0
            ), 'XYZ')
            upper_chest.rotation_quaternion = upper_chest_euler.to_quaternion()
            upper_chest.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Apply Neck & Head (Tiny living micro-tilts & gaze compensation)
        if neck:
            neck.rotation_mode = 'QUATERNION'
            neck_euler = Euler((
                math.radians(-0.3) * breath_factor,
                math.radians(0.5) * shift_sin,
                math.radians(-0.3) * shift_sin
            ), 'XYZ')
            neck.rotation_quaternion = neck_euler.to_quaternion()
            neck.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if head:
            head.rotation_mode = 'QUATERNION'
            head_euler = Euler((
                math.radians(-0.4) * breath_factor + math.radians(0.3) * math.sin(shift_theta * 2),
                math.radians(-0.6) * shift_sin,
                math.radians(0.5) * shift_sin
            ), 'XYZ')
            head.rotation_quaternion = head_euler.to_quaternion()
            head.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Apply Shoulders (Subtle rise with breathing)
        if l_shoulder and r_shoulder:
            l_shoulder.rotation_mode = 'QUATERNION'
            r_shoulder.rotation_mode = 'QUATERNION'
            s_lift = math.radians(0.5) * breath_factor
            l_shoulder.rotation_quaternion = Euler((0, 0, s_lift), 'XYZ').to_quaternion()
            r_shoulder.rotation_quaternion = Euler((0, 0, -s_lift), 'XYZ').to_quaternion()
            l_shoulder.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            r_shoulder.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Apply Relaxed Arms with subtle breath accompaniment
        for bone, q in base_pose.items():
            if bone and q:
                bone.rotation_mode = 'QUATERNION'
                bone.rotation_quaternion = q
                bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    # 3. Animate Natural Blinks on Face Mesh
    if face_mesh and face_mesh.data.shape_keys:
        sk_blocks = face_mesh.data.shape_keys.key_blocks
        blink_key = sk_blocks.get('blink') or sk_blocks.get('Fcl_EYE_Close')
        if blink_key:
            print(f"[CustomIdle] Keyframing blinks on shape key: {blink_key.name}")
            # Ensure neutral at start/end
            blink_key.value = 0.0
            blink_key.keyframe_insert("value", frame=0)
            blink_key.keyframe_insert("value", frame=TOTAL_FRAMES)

            # Blink 1 around 2.4s (frame 72)
            blink_key.value = 0.0
            blink_key.keyframe_insert("value", frame=68)
            blink_key.value = 1.0
            blink_key.keyframe_insert("value", frame=72)
            blink_key.value = 0.0
            blink_key.keyframe_insert("value", frame=76)

            # Blink 2 around 5.4s (frame 162)
            blink_key.value = 0.0
            blink_key.keyframe_insert("value", frame=158)
            blink_key.value = 1.0
            blink_key.keyframe_insert("value", frame=162)
            blink_key.value = 0.0
            blink_key.keyframe_insert("value", frame=166)

    # 4. Set Bezier Smoothing on All Curves
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
        # Blender 5.x layered action structure
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

    # 5. Export to VRMA using VRM Add-on
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
