bl_info = {
    "name": "Automotive Tools",
    "blender": (4, 2, 0),
    "category": "Object",
    "version": (3, 0),
    "author": "Your Name",
    "location": "View3D > Sidebar > AT",
    "description": "汽车数据处理工具集",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}

import bpy
import bmesh

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

        # 为每个对象创建顶点组
        for obj in selected_objects:
            if obj.type == 'MESH':
                vg = obj.vertex_groups.new(name=obj.name)
                vg.add(range(len(obj.data.vertices)), 1.0, 'REPLACE')

        # 执行合并
        bpy.ops.object.join()
        self.report({'INFO'}, "合并完成！顶点组已保留。")
        return {'FINISHED'}

class OBJECT_OT_select_vertex_group_elements(bpy.types.Operator):
    """根据顶点组选择元素"""
    bl_idname = "object.select_vertex_group_elements"
    bl_label = "选择顶点组元素"
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

        # 收集目标顶点组索引
        target_indices = set()
        select_mode = context.tool_settings.mesh_select_mode

        if select_mode[0]:  # 顶点模式
            for v in bm.verts:
                if v.select:
                    target_indices.update(v[deform_layer].keys())
        elif select_mode[1]:  # 边模式
            for e in bm.edges:
                if e.select:
                    for v in e.verts:
                        target_indices.update(v[deform_layer].keys())
        elif select_mode[2]:  # 面模式
            for f in bm.faces:
                if f.select:
                    for v in f.verts:
                        target_indices.update(v[deform_layer].keys())

        if not target_indices:
            self.report({'WARNING'}, "未找到关联顶点组！")
            return {'CANCELLED'}

        # 执行选择
        bpy.ops.mesh.select_all(action='DESELECT')
        for vg_idx in target_indices:
            if vg_idx >= len(obj.vertex_groups):
                continue
            for v in bm.verts:
                if vg_idx in v[deform_layer]:
                    v.select = True

        bmesh.update_edit_mesh(obj.data)
        self.report({'INFO'}, f"已选择 {len(target_indices)} 个顶点组的顶点")
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
        # 记录原始状态
        original_active = context.active_object
        original_mode = original_active.mode

        # 进入编辑模式（如果不在编辑模式）
        if original_mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        # 执行内置分离操作
        bpy.ops.mesh.separate(type='MATERIAL')

        # 返回对象模式
        bpy.ops.object.mode_set(mode='OBJECT')

        # 恢复原始活动对象（Blender默认会选择新对象，这里重置选择）
        bpy.ops.object.select_all(action='DESELECT')
        original_active.select_set(True)
        context.view_layer.objects.active = original_active

        # 恢复原始模式
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
        
        # 遍历所有选中对象
        for obj in context.selected_objects:
            if obj.type != 'MESH' or not obj.vertex_groups:
                continue

            # 使用bmesh高效访问数据
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            deform_layer = bm.verts.layers.deform.active
            used_groups = set()

            # 收集使用的顶点组索引
            if deform_layer:
                for v in bm.verts:
                    used_groups.update(v[deform_layer].keys())

            # 反向遍历删除空组
            removed = 0
            for vg in reversed(obj.vertex_groups):
                if vg.index not in used_groups:
                    obj.vertex_groups.remove(vg)
                    removed += 1

            bm.free()
            total_removed += removed
            print(f"对象 {obj.name} 移除了 {removed} 个空顶点组")

        self.report({'INFO'}, f"总计清理 {total_removed} 个空顶点组")
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
        col = layout.column(align=True)
        
        # 合并功能
        col.label(text="合并工具:")
        col.operator(OBJECT_OT_join_with_pregroups.bl_idname, icon='GROUP_VERTEX')
        
        # 选择功能
        col.separator()
        col.label(text="选择工具:")
        col.operator(OBJECT_OT_select_vertex_group_elements.bl_idname, icon='SELECT_SET')
        
        # 分离与清理
        col.separator()
        col.label(text="优化工具:")
        col.operator(OBJECT_OT_split_by_material.bl_idname, icon='MATERIAL_DATA')
        col.operator(OBJECT_OT_clean_empty_vertex_groups.bl_idname, icon='TRASH')

# ---------------------- 注册 ----------------------
classes = (
    OBJECT_OT_join_with_pregroups,
    OBJECT_OT_select_vertex_group_elements,
    OBJECT_OT_split_by_material,
    OBJECT_OT_clean_empty_vertex_groups,
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