# Automotive Tools 汽车数据处理工具集
## Introduction  简介

A Blender plugin designed for automotive industry practitioners, designed to make data organization and optimization of car models exported from Alias ​​or other industrial modeling software faster and more convenient  
为汽车行业从业者制作的Blender插件，旨在更快更方便的对从Alias或者其他的工业建模软件导出的汽车模型进行数据整理和优化  

## Download and Installation  下载与安装

1. 下载插件文件
2. 打开Blender首选项，选择插件，右上角下拉菜单选择从本地安装
3. 选择压缩包或者.py文件进行安装
4. 安装后将会在3D视图中侧边栏出现“**AT**”菜单

## Function Introduction  功能简介

### Merge and preserve vertex groups  合并并保留顶点组

合并多个物体的同时保留将物体以顶点组的形式储存，方便物体的选择

### Select by Vertex Group Elements  选择顶点组元素

在编辑模式中，选中点或者面，使用此命令可以快速选择该点或者面所在整个顶点组，快速选取部件

### Separation by material  按材质分离

按材质将合并的物体进行拆分

### Clean up empty vertex groups 清理空顶点组

清理所有所选物体的空顶点组

### Select non uniform scale 选择非常规缩放

选择缩放不为1的物体，作为导出前的检查项

### Rename to collection 按集合重命名

将选中物体及其数据按所属集合重命名，用于解决datasmith等导出后数据命名超过windows系统最大限制而报错的问题

### Triangulate objects 三角化

为所有选中物体添加三角化修改器，用于解决datasmith导出后平滑组被破坏的问题
