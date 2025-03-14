bl_info = {
    "name": "Automotive Tools",
    "blender": (4, 2, 0),
    "category": "Object",
    "version": (1, 1),
    "author": "CarlMarksWX",
    "location": "View3D > Sidebar > AT",
    "description": "汽车数据处理工具集",
    "warning": "本插件无法及时随版本更新，如遇报错请至项目网站查询更新",
    "github_url": "https://github.com/CarlMarkswx/AutomotiveTools_for_blender/",
}

import bpy
import bmesh
from collections import defaultdict

# ---------------------- 核心功能 ----------------------
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

def register():
    bpy.utils.register_class(OBJECT_OT_select_vertex_group_elements)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_select_vertex_group_elements)

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
    
# ---------------------- 用户界面 ----------------------
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
        col.operator(OBJECT_OT_join_with_pregroups.bl_idname, icon='AUTOMERGE_ON')
        col.operator(OBJECT_OT_select_vertex_group_elements.bl_idname, icon='GROUP_VERTEX')
        col.operator(OBJECT_OT_clean_empty_vertex_groups.bl_idname, icon='BRUSH_DATA')
        col.operator(OBJECT_OT_clear_custom_normals.bl_idname, icon='NORMALS_VERTEX_FACE')  # 新增按钮

        # 材质操作
        mat_box = main_box.box()
        mat_box.label(text="材质操作", icon='MATERIAL')
        mat_box.operator(OBJECT_OT_split_by_material.bl_idname, icon='MOD_EXPLODE')

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
        
# ---------------------- 注册 ----------------------
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
    VIEW3D_PT_join_tools,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()