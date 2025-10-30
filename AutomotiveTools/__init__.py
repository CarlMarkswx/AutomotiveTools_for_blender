bl_info = {
    "name": "Automotive Tools",
    "blender": (4, 5, 0),
    "category": "Object",
    "version": (1, 2, 1),
    "author": "CarlMarksWX",
    "location": "View3D > Sidebar > AT",
    "description": "汽车数据处理工具集",
    "warning": "本插件无法及时随版本更新，如遇报错请至项目网站查询更新",
    "github_url": "https://github.com/CarlMarkswx/AutomotiveTools_for_blender/",
}
import bpy
import re
import bmesh
from collections import defaultdict

# ---------------------- 核心功能 (包含所有修正和新增) ----------------------
class OBJECT_OT_join_with_pregroups(bpy.types.Operator):
    """合并对象并保留原始顶点组"""
    bl_idname = "object.join_with_pregroups"
    bl_label = "合并并保留顶点组"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        selected_objects = context.selected_objects.copy()
        if len(selected_objects) < 2:
            self.report({'WARNING'}, "请至少选中两个对象！")
            return {'CANCELLED'}
        for obj in selected_objects:
            if obj.type == 'MESH':
                vg = obj.vertex_groups.new(name=obj.name)
                vg.add(range(len(obj.data.vertices)), 1.0, 'REPLACE')
        bpy.ops.object.join()
        self.report({'INFO'}, "合并完成！顶点组已保留。")
        return {'FINISHED'}

class OBJECT_OT_select_vertex_group_elements(bpy.types.Operator):
    """根据顶点组选择面"""
    bl_idname = "object.select_vertex_group_elements"
    bl_label = "选择顶点组面"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'
    def execute(self, context):
        obj = context.active_object
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)
        deform_layer = bm.verts.layers.deform.active
        if not deform_layer:
            self.report({'WARNING'}, "没有顶点组数据！")
            return {'CANCELLED'}
        target_indices = set()
        select_mode = context.tool_settings.mesh_select_mode
        # 根据不同的选择模式，获取选中元素所属的顶点组索引
        if select_mode[0]:
            for v in bm.verts:
                if v.select:
                    target_indices.update(v[deform_layer].keys())
        elif select_mode[1]:
            for e in bm.edges:
                if e.select:
                    for v in e.verts:
                        target_indices.update(v[deform_layer].keys())
        elif select_mode[2]:
            for f in bm.faces:
                if f.select:
                    for v in f.verts:
                        target_indices.update(v[deform_layer].keys())
        if not target_indices:
            self.report({'WARNING'}, "未找到关联顶点组！")
            return {'CANCELLED'}
        # 筛选出合法的顶点组索引（防止因权重数据异常而超出范围）
        target_indices = {vg_idx for vg_idx in target_indices if vg_idx < len(obj.vertex_groups)}
        bpy.ops.mesh.select_all(action='DESELECT')
        # 遍历所有面，检查是否存在一个目标顶点组，使得面上所有顶点均属于该顶点组
        for f in bm.faces:
            for vg_idx in target_indices:
                if all(vg_idx in v[deform_layer] for v in f.verts):
                    f.select = True
                    break  # 一个顶点组满足条件即可
        bmesh.update_edit_mesh(obj.data)
        self.report({'INFO'}, f"已选择 {len(target_indices)} 个顶点组对应的面")
        return {'FINISHED'}

class OBJECT_OT_split_by_material(bpy.types.Operator):
    """按材质分离对象"""
    bl_idname = "object.split_by_material"
    bl_label = "按材质分离"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.material_slots
    def execute(self, context):
        original_active = context.active_object
        original_mode = original_active.mode
        if original_mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.separate(type='MATERIAL')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        original_active.select_set(True)
        context.view_layer.objects.active = original_active
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        self.report({'INFO'}, "已按材质分离（保留默认命名）")
        return {'FINISHED'}

class OBJECT_OT_clean_empty_vertex_groups(bpy.types.Operator):
    """清理空顶点组"""
    bl_idname = "object.clean_empty_vertex_groups"
    bl_label = "清理空顶点组"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        return any(obj.type == 'MESH' for obj in context.selected_objects)
    def execute(self, context):
        total_removed = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH' or not obj.vertex_groups:
                continue
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            deform_layer = bm.verts.layers.deform.active
            used_groups = set()
            if deform_layer:
                for v in bm.verts:
                    used_groups.update(v[deform_layer].keys())
            removed = 0
            for vg in reversed(obj.vertex_groups):
                if vg.index not in used_groups:
                    obj.vertex_groups.remove(vg)
                    removed += 1
            bm.free()
            total_removed += removed
        self.report({'INFO'}, f"总计清理 {total_removed} 个空顶点组")
        return {'FINISHED'}

class OBJECT_OT_rename_to_collection(bpy.types.Operator):
    """将选中物体及其数据按所属集合重命名"""
    bl_idname = "object.rename_to_collection"
    bl_label = "按集合重命名"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        return context.selected_objects
    def execute(self, context):
        collection_groups = defaultdict(list)
        renamed_count = 0
        for obj in context.selected_objects:
            if obj.users_collection:
                coll_name = obj.users_collection[0].name
            else:
                coll_name = "未分类"
            collection_groups[coll_name].append(obj)
        for coll_name, objs in collection_groups.items():
            for idx, obj in enumerate(objs, 1):
                new_name = f"{coll_name}_{idx:03d}"
                try:
                    if obj.data:
                        if obj.data.users > 1:
                            obj.data = obj.data.copy()
                        obj.data.name = new_name
                    obj.name = new_name
                    renamed_count += 1
                except Exception as e:
                    self.report({'ERROR'}, f"重命名失败: {str(e)}")
                    continue
        self.report({'INFO'}, f"成功重命名 {renamed_count} 个物体")
        return {'FINISHED'}

class OBJECT_OT_select_non_uniform_scale(bpy.types.Operator):
    """选择所有缩放值不等于1的物体"""
    bl_idname = "object.select_non_uniform_scale"
    bl_label = "选择非常规缩放"
    bl_options = {'REGISTER', 'UNDO'}
    tolerance: bpy.props.FloatProperty(
        name="容差",
        default=0.001,
        min=0.0001,
        max=1.0,
        description="允许的误差范围"
    )
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    def execute(self, context):
        for obj in context.view_layer.objects:
            obj.select_set(False)
        selected_count = 0
        for obj in context.scene.objects:
            if (abs(obj.scale.x - 1.0) > self.tolerance or 
                abs(obj.scale.y - 1.0) > self.tolerance or 
                abs(obj.scale.z - 1.0) > self.tolerance):
                obj.select_set(True)
                selected_count += 1
        self.report({'INFO'}, f"已选择 {selected_count} 个非常规缩放物体")
        return {'FINISHED'}

class OBJECT_OT_triangulate_objects(bpy.types.Operator):
    """为所有选中物体添加三角化修改器"""
    bl_idname = "object.triangulate_objects"
    bl_label = "添加三角化"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                modifier = obj.modifiers.new(name="Triangulate", type='TRIANGULATE')
                modifier.keep_custom_normals = True
        self.report({'INFO'}, "已添加三角化修改器")
        return {'FINISHED'}

class OBJECT_OT_remove_triangulate(bpy.types.Operator):
    """删除所有三角化修改器"""
    bl_idname = "object.remove_triangulate"
    bl_label = "删除三角化"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        removed_count = 0
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for mod in reversed(obj.modifiers):
                    if mod.type == 'TRIANGULATE':
                        obj.modifiers.remove(mod)
                        removed_count += 1
        self.report({'INFO'}, f"已删除 {removed_count} 个三角化修改器")
        return {'FINISHED'}

class OBJECT_OT_clear_custom_normals(bpy.types.Operator):
    """清除自定义拆边法线数据"""
    bl_idname = "object.clear_custom_normals"
    bl_label = "清除拆边法线"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        return any(obj.type == 'MESH' for obj in context.selected_objects)
    def execute(self, context):
        cleared_count = 0
        original_active = context.active_object
        selected_objects = context.selected_objects.copy()
        # 使用临时上下文覆盖进行批量处理
        for obj in selected_objects:
            if obj.type != 'MESH':
                continue
            try:
                # 创建临时上下文
                override = {
                    'active_object': obj,
                    'object': obj,
                    'selected_objects': [obj]
                }
                # 直接调用清除操作符
                with context.temp_override(**override):
                    bpy.ops.mesh.customdata_custom_splitnormals_clear()
                cleared_count += 1
                # 兼容处理：清除残留数据
                if hasattr(obj.data, "use_auto_smooth"):
                    obj.data.use_auto_smooth = False
                if hasattr(obj.data, "has_custom_normals"):
                    obj.data.has_custom_normals = False
            except Exception as e:
                self.report({'WARNING'}, f"处理 {obj.name} 失败: {str(e)}")
                continue
        # 恢复原始上下文
        context.view_layer.objects.active = original_active
        for obj in selected_objects:
            obj.select_set(True)
        self.report({'INFO'}, f"已清除 {cleared_count}/{len(selected_objects)} 个物体的拆边法线")
        return {'FINISHED'}

class OBJECT_OT_select_multi_material(bpy.types.Operator):
    """选择所有包含多个材质插槽的物体"""
    bl_idname = "object.select_multi_material"
    bl_label = "选择多材质物体"
    bl_options = {'REGISTER', 'UNDO'}
    min_slots: bpy.props.IntProperty(
        name="最小插槽数",
        default=2,
        min=1,
        description="需要选择的最小材质插槽数量"
    )
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    def execute(self, context):
        # 记录原始选择
        original_selection = context.selected_objects.copy()
        selected_count = 0
        # 清空当前选择
        bpy.ops.object.select_all(action='DESELECT')
        # 遍历所有可见物体
        for obj in context.visible_objects:
            if obj.type == 'MESH' and len(obj.material_slots) >= self.min_slots:
                obj.select_set(True)
                selected_count += 1
        # 如果没有选中物体则恢复原选择
        if selected_count == 0:
            for obj in original_selection:
                obj.select_set(True)
            self.report({'WARNING'}, "未找到多材质物体")
            return {'CANCELLED'}
        self.report({'INFO'}, f"已选中 {selected_count} 个多材质物体")
        return {'FINISHED'}

class OBJECT_OT_empty_to_collection(bpy.types.Operator):
    """将空物体的父子层级结构转换为 Collection 嵌套结构"""
    bl_idname = "object.empty_to_collection"
    bl_label = "空物体转 Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # 1. 收集所有 Empty 物体
        empty_objects = [obj for obj in bpy.data.objects if obj.type == 'EMPTY']

        if not empty_objects:
            self.report({'INFO'}, "场景中没有找到空物体。")
            return {'CANCELLED'}

        # 2. 构建父子关系映射
        empty_children_map = defaultdict(list)
        root_empties = []

        for obj in empty_objects:
            parent = obj.parent
            if parent and parent in empty_objects:
                # 如果父级也是 Empty，则添加到父级的子列表中
                empty_children_map[parent].append(obj)
            else:
                # 如果没有父级，或者父级不是 Empty，则为根节点
                root_empties.append(obj)

        # 3. 递归函数：处理单个 Empty 及其子层级
        def process_empty(empty_obj, parent_collection):
            # a. 创建对应此 Empty 的 Collection
            collection_name = empty_obj.name
            new_collection = bpy.data.collections.new(collection_name)

            # b. 将新 Collection 链接到父级 Collection（或场景根集合）
            parent_collection.children.link(new_collection)

            # c. 移动 Empty 的子物体（包括非 Empty 和子 Empty）到新 Collection
            for child_obj in empty_obj.children:
                # 从其当前所有父级 Collection 中移除
                for col in child_obj.users_collection:
                    col.objects.unlink(child_obj)
                # 添加到新创建的 Collection
                new_collection.objects.link(child_obj)

            # d. 递归处理子 Empty 物体
            for child_empty in empty_children_map[empty_obj]:
                process_empty(child_empty, new_collection)

            # e. 标记此 Empty 为待删除
            # (在处理完所有层级后统一删除，避免在迭代时修改集合)
            empties_to_delete.append(empty_obj)

        # 4. 存储待删除的 Empty 物体
        empties_to_delete = []

        # 5. 从根节点开始处理
        for root_empty in root_empties:
            process_empty(root_empty, context.scene.collection)

        # 6. 删除所有被处理的 Empty 物体
        for empty_obj in empties_to_delete:
            bpy.data.objects.remove(empty_obj, do_unlink=True)

        self.report({'INFO'}, f"已将 {len(empties_to_delete)} 个空物体及其层级结构转换为 Collection。")
        return {'FINISHED'}

class OBJECT_OT_merge_duplicate_materials(bpy.types.Operator):
    """根据指定后缀合并重复材质（如 .001 / _001 / -01）"""
    bl_idname = "object.merge_duplicate_materials"
    bl_label = "合并重复材质"
    bl_options = {'UNDO'} # 移除 'REGISTER' 以避免弹窗

    def execute(self, context):
        # 从场景属性获取后缀样例
        suffix = context.scene.merge_mat_suffix_pattern.strip()
        # print(f"DEBUG: 输入的后缀样例是: '{suffix}'") # 调试输出
        if not suffix:
            self.report({'ERROR'}, "场景属性中后缀样例为空。")
            return {'CANCELLED'}

        # --- 从后缀样例中提取静态部分和数字部分 ---
        # 例如，suffix = ".001" -> static_part = ".", numeric_part = "001"
        # 例如，suffix = "_001" -> static_part = "_", numeric_part = "001"
        # 例如，suffix = "-01" -> static_part = "-", numeric_part = "01"
        # 使用正则找到后缀末尾的数字部分
        numeric_match = re.search(r'(\d+)$', suffix)
        if not numeric_match:
             self.report({'ERROR'}, f"后缀样例 '{suffix}' 末尾必须包含数字。")
             return {'CANCELLED'}
        numeric_part = numeric_match.group(1)
        static_part = suffix[:-len(numeric_part)] # 获取数字之前的静态部分
        # print(f"DEBUG: 解析出的 static_part 是: '{static_part}'") # 调试输出

        if not static_part: # 如果静态部分为空，说明整个后缀都是数字，这不合理
            self.report({'ERROR'}, f"后缀样例 '{suffix}' 必须包含非数字部分。")
            return {'CANCELLED'}

        # --- 构造匹配模式 ---
        # 模式匹配：基础名 + 静态后缀 + 任意数字 (至少一个)
        # 例如，static_part = "." -> 模式匹配 "基础名.数字"
        pattern = re.compile(rf"^(.+){re.escape(static_part)}\d+$")
        # print(f"DEBUG: 构造的正则模式是: '{pattern.pattern}'") # 调试输出

        # --- 筛选有用户的材质，并同时检查基础材质 ---
        all_mats_with_users = [m for m in bpy.data.materials if m.users > 0]
        if not all_mats_with_users:
            self.report({'WARNING'}, "没有找到被使用的材质。")
            return {'CANCELLED'}

        # --- 根据提取的静态部分进行分组 (只对 *匹配模式* 的有用户材质进行分组) ---
        grouped = defaultdict(list)
        for mat in all_mats_with_users:
            match = pattern.match(mat.name)
            if match:
                base_name = match.group(1)
                grouped[base_name].append(mat)

        # --- 修正点：检查基础材质是否也在有用户的材质列表中 ---
        # 如果基础名材质存在且有用户，将其加入对应的分组列表
        for base_name in list(grouped.keys()): # 使用 list 避免在迭代时修改字典
            base_mat_candidate = bpy.data.materials.get(base_name)
            if base_mat_candidate and base_mat_candidate.users > 0:
                 # 将基础材质添加到其对应的分组列表中
                 grouped[base_name].append(base_mat_candidate)
                 # print(f"DEBUG: 将基础材质 '{base_name}' (users={base_mat_candidate.users}) 加入分组。") # 调试输出

        # --- 过滤掉成员少于2个的分组 ---
        grouped = {k: v for k, v in grouped.items() if len(v) >= 2}

        if not grouped:
            self.report({'WARNING'}, f"未找到符合模式 '{static_part}+数字' 且需要合并的重复材质。")
            return {'CANCELLED'}

        merged_count = 0
        removed_count = 0

        for base_name, dup_list in grouped.items():
            # print(f"DEBUG: 处理分组 '{base_name}', 材质: {[m.name for m in dup_list]}") # 调试输出
            # --- 优先查找 *存在且有用户* 的基础名材质作为主材质 ---
            base_mat = None
            for mat in dup_list:
                 if mat.name == base_name and mat.users > 0:
                     base_mat = mat
                     # print(f"DEBUG: 选择存在的、有用户的 '{base_name}' 作为主材质。") # 调试输出
                     break

            # --- 如果没有找到，则从分组列表中选择一个作为主材质 ---
            if base_mat is None:
                 dup_list_sorted = sorted(dup_list, key=lambda x: x.name)
                 base_mat = dup_list_sorted[0]
                 dup_list_to_merge = [m for m in dup_list_sorted if m != base_mat]
                 # print(f"DEBUG: 未找到有用户的 '{base_name}'，选择 '{base_mat.name}' 作为主材质。") # 调试输出
            else:
                 # 如果找到了 base_mat，则将分组内其他材质合并到它
                 dup_list_to_merge = [m for m in dup_list if m != base_mat]

            # --- 执行合并 ---
            for dup_mat in dup_list_to_merge:
                 # print(f"DEBUG: 将 '{dup_mat.name}' 合并到 '{base_mat.name}'") # 调试输出
                 for obj in bpy.data.objects:
                    if not hasattr(obj.data, "materials"):
                        continue
                    for slot in obj.material_slots:
                        if slot.material == dup_mat:
                            slot.material = base_mat
                 merged_count += 1
                 try:
                     bpy.data.materials.remove(dup_mat)
                     removed_count += 1
                 except:
                     pass # 如果删除失败（例如，被其他地方引用），则跳过

        self.report({'INFO'}, f"已合并 {merged_count} 个材质，删除 {removed_count} 个重复项。")
        return {'FINISHED'}

class OBJECT_OT_clean_unused_material_slots(bpy.types.Operator):
    """清理所选物体中未被任何面使用的材质插槽（不会清理材质本身）"""
    bl_idname = "object.clean_unused_material_slots"
    bl_label = "清理未使用材质插槽"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        sel = context.selected_objects
        cleaned = 0
        # 需要在 object 模式下并且对象为活动对象才能使用 material_slot_remove 操作
        prev_active = context.view_layer.objects.active
        prev_mode = context.mode
        for obj in sel:
            if obj.type != 'MESH' or not obj.material_slots:
                continue
            # 计算哪些插槽被使用（polygon.material_index）
            used_indices = set(poly.material_index for poly in obj.data.polygons)
            total_slots = len(obj.material_slots)
            if len(used_indices) == total_slots:
                continue  # 全部使用，无需清理
            # 选中并设置为活动对象
            for o in context.selected_objects:
                o.select_set(False)
            obj.select_set(True)
            context.view_layer.objects.active = obj
            # 确保处于 OBJECT 模式
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            # 倒序删除未使用插槽，使用 bpy.ops 保证数据和 UI 正确刷新
            for i in range(total_slots - 1, -1, -1):
                if i not in used_indices:
                    # set active material index 然后删除
                    obj.active_material_index = i
                    try:
                        bpy.ops.object.material_slot_remove()
                        cleaned += 1
                    except Exception as e:
                        self.report({'WARNING'}, f"{obj.name} 删除材质槽索引 {i} 失败: {e}")
        # 恢复原始上下文选择与活动对象
        for o in sel:
            o.select_set(True)
        if prev_active:
            context.view_layer.objects.active = prev_active
        if prev_mode != context.mode:
            try:
                bpy.ops.object.mode_set(mode=prev_mode)
            except:
                pass
        self.report({'INFO'}, f"已清理 {cleaned} 个未使用材质插槽（仅针对所选物体）")
        return {'FINISHED'}

# --- 修正：自动编组操作符 (增加确认弹窗、默认简单模式、执行后清理空集合) ---
class OBJECT_OT_auto_group_objects(bpy.types.Operator):
    """根据物体名称自动创建Collection并嵌套分组"""
    bl_idname = "object.auto_group_objects"
    bl_label = "自动编组"
    bl_options = {'REGISTER'} # 移除 'UNDO'，因为确认弹窗后执行，不需要额外的撤销步骤

    def invoke(self, context, event):
        # 弹出确认对话框
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        # 在弹窗中显示警告信息
        layout = self.layout
        col = layout.column()
        col.label(text="此操作将重置视图层中的所有层级结构！", icon='ERROR')
        col.label(text="建议仅在导入新数据后使用。")
        col.separator()
        col.label(text=f"当前模式: {'简单' if context.scene.auto_group_mode == 'simple' else '复杂'}")
        col.prop(context.scene, "auto_group_mode", text="") # 显示当前模式选择

    def execute(self, context):
        # 确认后执行
        mode = context.scene.auto_group_mode
        # --- 修正点：遍历 bpy.data.objects 而不是 context.scene.objects ---
        # 这样可以处理所有物体，无论它们当前在哪个 Collection 中
        objects_to_process = [obj for obj in bpy.data.objects if obj.type == 'MESH']
        # --- 结束修正 ---

        # 存储 Collection 引用，避免重复查找
        collection_cache = {}

        for obj in objects_to_process:
            name_parts = obj.name.split('_')
            if len(name_parts) < 2:
                continue

            # --- 计算目标 Collection 路径 ---
            if mode == 'simple':
                # 目标路径: Scene -> Part_Subpart
                target_collection_path = ["", "_".join(name_parts[:-1])] # "" 代表根集合
            else: # mode == 'complex'
                # 目标路径: Scene -> Part -> Part_Subpart
                collection_path_parts = name_parts[:-1]
                if not collection_path_parts:
                    continue
                # "" 代表根集合, Part, Part_Subpart
                target_collection_path = [""] + collection_path_parts

            # --- 获取当前 Collection 路径 ---
            current_collections = list(obj.users_collection)
            if not current_collections:
                # 如果物体不在任何 Collection 中，当前路径为空
                current_collection_path = [""]
            else:
                # 获取物体第一个父级 Collection
                current_child_collection = current_collections[0]
                # 追溯到根集合，构建当前路径
                current_path_parts = [current_child_collection.name]
                parent_collection = self.find_parent_collection(context.scene.collection, current_child_collection)
                while parent_collection:
                     current_path_parts.insert(0, parent_collection.name) # 插入到开头
                     grandparent = self.find_parent_collection(context.scene.collection, parent_collection)
                     parent_collection = grandparent
                # 如果追溯到了根集合，路径应以 "" 开头
                if current_path_parts and current_path_parts[0] != "":
                    current_path_parts.insert(0, "") # 插入根集合标识符
                current_collection_path = current_path_parts

            # --- 比较路径 ---
            # print(f"DEBUG: 物体 '{obj.name}' 当前路径: {current_collection_path}, 目标路径: {target_collection_path}") # 调试输出
            if current_collection_path == target_collection_path:
                # print(f"DEBUG: 物体 '{obj.name}' 路径已匹配，跳过。") # 调试输出
                continue # 路径一致，无需操作

            # --- 路径不一致，需要重组 ---
            # 1. 根据目标路径创建或获取目标 Collection
            target_collection = self.get_or_create_collection_by_path(context, target_collection_path, collection_cache)

            # 2. 将物体从当前所有 Collection 中移除
            for col in list(obj.users_collection):
                col.objects.unlink(obj)

            # 3. 将物体链接到计算出的目标 Collection
            target_collection.objects.link(obj)

        # --- 新增：执行后清理空集合 ---
        self.cleanup_empty_collections(context)

        self.report({'INFO'}, f"自动编组完成 (模式: {'简单' if mode == 'simple' else '复杂'})。已清理空集合。")
        return {'FINISHED'}

    def find_parent_collection(self, root_collection, target_collection):
        """查找 target_collection 的父级 Collection"""
        def search_parent(parent, target):
            for child in parent.children:
                if child == target:
                    return parent
                found = search_parent(child, target)
                if found:
                    return found
            return None
        return search_parent(root_collection, target_collection)

    def get_or_create_collection_by_path(self, context, path, cache):
        """根据路径列表创建或获取 Collection"""
        if not path or path[0] != "": # 路径应以根集合标识符 "" 开头
             raise ValueError(f"Invalid path: {path}")

        current_parent = context.scene.collection
        full_path_key = ""

        for i, part_name in enumerate(path[1:], 1): # 跳过根标识符 ""
            full_path_key += f"__{part_name}" # 使用特殊分隔符构建缓存键
            collection = cache.get(full_path_key)
            if not collection:
                # 在当前父级下查找
                collection = current_parent.children.get(part_name)
                if not collection:
                    # 创建新 Collection
                    collection = bpy.data.collections.new(part_name)
                    current_parent.children.link(collection)
                cache[full_path_key] = collection

            current_parent = collection

        return current_parent


    def cleanup_empty_collections(self, context):
        """递归查找并删除空的Collection"""
        def is_collection_empty(collection):
            # 检查 Collection 是否包含物体或子 Collection
            return (not collection.objects and
                    not any(is_collection_not_empty_recursive(sub_col) for sub_col in collection.children))

        def is_collection_not_empty_recursive(collection):
            # 辅助函数：检查 Collection 是否非空（包含物体或包含非空子 Collection）
            if collection.objects:
                return True
            for sub_col in collection.children:
                if is_collection_not_empty_recursive(sub_col):
                    return True
            return False

        # 从场景根集合开始
        root_collections = list(context.scene.collection.children)

        # 递归查找空集合
        empty_collections = []
        def find_empty_recursive(collection):
            for sub_col in collection.children:
                find_empty_recursive(sub_col)
                if is_collection_empty(sub_col):
                    empty_collections.append(sub_col)
            # 检查根集合本身是否为空（虽然不太可能，但保险起见）
            if is_collection_empty(collection):
                empty_collections.append(collection)

        for root_col in root_collections:
            find_empty_recursive(root_col)

        # 删除找到的空集合
        deleted_count = 0
        for empty_col in empty_collections:
            try:
                bpy.data.collections.remove(empty_col)
                deleted_count += 1
            except:
                pass # 如果删除失败（例如，被其他地方引用），则跳过

        # print(f"DEBUG: 清理了 {deleted_count} 个空集合。") # 调试输出

# --- 新增：手动清理空集合操作符 ---
class OBJECT_OT_cleanup_empty_collections(bpy.types.Operator):
    """手动清理场景中所有空的Collection"""
    bl_idname = "object.cleanup_empty_collections"
    bl_label = "清理空集合"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # 重用 auto_group_objects 中的清理逻辑
        # 也可以创建一个独立的清理函数
        def is_collection_empty(collection):
            return (not collection.objects and
                    not any(is_collection_not_empty_recursive(sub_col) for sub_col in collection.children))

        def is_collection_not_empty_recursive(collection):
            if collection.objects:
                return True
            for sub_col in collection.children:
                if is_collection_not_empty_recursive(sub_col):
                    return True
            return False

        root_collections = list(context.scene.collection.children)
        empty_collections = []

        def find_empty_recursive(collection):
            for sub_col in collection.children:
                find_empty_recursive(sub_col)
                if is_collection_empty(sub_col):
                    empty_collections.append(sub_col)
            if is_collection_empty(collection):
                empty_collections.append(collection)

        for root_col in root_collections:
            find_empty_recursive(root_col)

        deleted_count = 0
        for empty_col in empty_collections:
            try:
                bpy.data.collections.remove(empty_col)
                deleted_count += 1
            except:
                pass

        self.report({'INFO'}, f"已手动清理 {deleted_count} 个空集合。")
        return {'FINISHED'}


# ---------------------- 用户界面 (包含 UI 修正和新增按钮) ----------------------
class VIEW3D_PT_join_tools(bpy.types.Panel):
    bl_label = "Automotive Tools"
    bl_idname = "VIEW3D_PT_join_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AT"
    def draw(self, context):
        layout = self.layout
        # ========== 数据处理 ==========
        main_box = layout.box()
        main_box.label(text="数据处理", icon='TOOL_SETTINGS')
        # 模型操作
        model_box = main_box.box()
        model_box.label(text="模型操作", icon='MESH_DATA')
        col = model_box.column(align=True)
        # col.operator(OBJECT_OT_empty_to_collection.bl_idname, icon='OUTLINER_OB_EMPTY') # 移除此行
        col.operator(OBJECT_OT_join_with_pregroups.bl_idname, icon='AUTOMERGE_ON')
        col.operator(OBJECT_OT_select_vertex_group_elements.bl_idname, icon='GROUP_VERTEX')
        col.operator(OBJECT_OT_clean_empty_vertex_groups.bl_idname, icon='BRUSH_DATA')
        col.operator(OBJECT_OT_clear_custom_normals.bl_idname, icon='NORMALS_VERTEX_FACE')

        # --- 修正：重组结构 UI ---
        restructure_box = main_box.box()
        restructure_box.label(text="重组结构", icon='OUTLINER_COLLECTION')
        restructure_col = restructure_box.column(align=True)
        # 空物体转 Collection
        restructure_col.operator(OBJECT_OT_empty_to_collection.bl_idname, icon='OUTLINER_OB_EMPTY')
        # 自动编组
        auto_group_row = restructure_col.row(align=True)
        auto_group_row.prop(context.scene, "auto_group_mode", text="") # text="" 隐藏属性名称标签
        auto_group_row.operator(OBJECT_OT_auto_group_objects.bl_idname, text="执行自动编组", icon='PASTEDOWN')
        # 手动清理空集合按钮
        restructure_col.operator(OBJECT_OT_cleanup_empty_collections.bl_idname, text="清理空集合", icon='TRASH')

        # 材质操作
        mat_box = main_box.box()
        mat_box.label(text="材质操作", icon='MATERIAL')
        mat_col = mat_box.column(align=True)

        # --- 合并重复材质 UI (已修正) ---
        # 1. 独立的按钮行
        mat_col.operator(OBJECT_OT_merge_duplicate_materials.bl_idname, text="合并重复材质", icon='NODE_MATERIAL')

        # 2. 输入框行，带标签和信息图标
        input_row = mat_col.row(align=True)
        input_row.prop(context.scene, "merge_mat_suffix_pattern", text="命名规律示例")
        input_row.operator("wm.context_toggle", icon='INFO', text="", depress=context.scene.show_merge_help).data_path = "scene.show_merge_help"

        # 3. 可选的帮助说明框
        if context.scene.show_merge_help:
            help_box = mat_col.box()
            help_box.label(text="示例：", icon='QUESTION')
            help_box.label(text="• .001 → 匹配 Material.001, Material.002 ...")
            help_box.label(text="• _001 → 匹配 Wheel_001, Wheel_002 ...")
            help_box.label(text="• -01 → 匹配 Door-01, Door-02 ...")
            help_box.label(text="提示：仅处理当前场景中有用户的材质。")
        # --- 结束合并重复材质 UI ---

        mat_col.operator(OBJECT_OT_clean_unused_material_slots.bl_idname, icon='BRUSH_DATA')
        mat_col.operator(OBJECT_OT_split_by_material.bl_idname, icon='MOD_EXPLODE')
        mat_col.operator(OBJECT_OT_select_multi_material.bl_idname, icon='MATERIAL_DATA')
        mat_col.prop(context.scene, 'at_multi_material_threshold', slider=True)

        # ========== 导出前检查 ==========
        export_box = layout.box()
        export_box.label(text="导出前检查", icon='EXPORT')
        # 检查工具
        check_box = export_box.box()
        check_box.label(text="模型检查", icon='VIEWZOOM')
        check_box.operator(OBJECT_OT_select_non_uniform_scale.bl_idname, icon='CON_SIZELIKE')
        # 优化工具
        optimize_box = export_box.box()
        optimize_box.label(text="导出优化", icon='MODIFIER')
        col = optimize_box.column(align=True)
        col.operator(OBJECT_OT_rename_to_collection.bl_idname, icon='OUTLINER_COLLECTION')
        col.operator(OBJECT_OT_triangulate_objects.bl_idname, icon='MOD_TRIANGULATE')
        col.operator(OBJECT_OT_remove_triangulate.bl_idname, icon='X')


# ---------------------- 注册 (包含新增类和属性) ----------------------
classes = (
    OBJECT_OT_join_with_pregroups,
    OBJECT_OT_select_vertex_group_elements,
    OBJECT_OT_split_by_material,
    OBJECT_OT_clean_empty_vertex_groups,
    OBJECT_OT_select_non_uniform_scale,
    OBJECT_OT_rename_to_collection,
    OBJECT_OT_triangulate_objects,
    OBJECT_OT_remove_triangulate,
    OBJECT_OT_clear_custom_normals,
    OBJECT_OT_select_multi_material,
    OBJECT_OT_empty_to_collection,
    OBJECT_OT_merge_duplicate_materials,
    OBJECT_OT_clean_unused_material_slots,
    OBJECT_OT_auto_group_objects, # 新增
    OBJECT_OT_cleanup_empty_collections, # 新增
    VIEW3D_PT_join_tools,
)

# 添加场景属性控制阈值
bpy.types.Scene.at_multi_material_threshold = bpy.props.IntProperty(
    name="材质插槽阈值",
    default=2,
    min=1,
    max=32,
    description="选择材质插槽数量超过此值的物体"
)

# 添加场景属性用于存储后缀样例 (默认值为 .001)
bpy.types.Scene.merge_mat_suffix_pattern = bpy.props.StringProperty(
    name="合并材质后缀",
    description="用于匹配重复材质的后缀样例（例如 .001, _001, -01）",
    default=".001"
)

# 添加场景属性用于控制帮助说明的显示/隐藏
bpy.types.Scene.show_merge_help = bpy.props.BoolProperty(
    name="显示合并材质帮助",
    description="展开或隐藏合并材质的示例说明",
    default=False
)

# --- 修正：场景属性用于控制自动编组模式 (使用 EnumProperty, 默认 'simple', 修复 if obj. 语法错误) ---
bpy.types.Scene.auto_group_mode = bpy.props.EnumProperty(
    name="自动编组模式",
    description="选择自动编组的模式",
    items=[
        ('simple', "简单模式", "创建一级Collection (Part_Subpart)", 'TRIA_RIGHT', 0),
        ('complex', "复杂模式", "根据名称结构创建嵌套Collection (Part -> Part_Subpart -> ObjectName)", 'TRIA_DOWN', 1),
    ],
    default='simple' # 修正：默认为简单模式
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.at_multi_material_threshold
    del bpy.types.Scene.merge_mat_suffix_pattern
    del bpy.types.Scene.show_merge_help
    del bpy.types.Scene.auto_group_mode # 修正

if __name__ == "__main__":
    register()