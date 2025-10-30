# 🚗 Automotive Tools — Data Processing Toolkit for Automotive 3D Models

> 🇨🇳 **中文版本在此:** [点击查看中文版 README](./README.md)  
> 📦 Current Version: **v1.2.1** | Compatible with **Blender 4.5**

---

## 🧩 Introduction

**Automotive Tools** is a Blender add-on designed for professionals in the automotive industry.  
It streamlines data cleanup, structure optimization, and export preparation for car models  
imported from **Alias, ICEM, CATIA, NX**, and other industrial modeling software.

---

## 📥 Download & Installation

1. Download the add-on file (`.zip` package or `.py` file).  
2. Open **Blender → Edit → Preferences → Add-ons**.  
3. Click “Install” in the top-right corner and select the downloaded file.  
4. Once enabled, the **“AT”** panel will appear in the **3D Viewport Sidebar (N)**.

---

## ⚙️ Feature Overview

### 🧱 Data Processing
* **Merge and Preserve Vertex Groups**: Merge selected objects and retain original vertex groups as object names for easy selection.  
* **Select by Vertex Group Elements**: In Edit Mode, select all vertices/faces influenced by the active vertex group.  
* **Separate by Material**: Split objects into separate meshes based on assigned materials (preserving default naming).  
* **Clean Empty Vertex Groups**: Remove vertex groups that are not assigned to any vertices.  
* **Clear Custom Split Normals**: Remove custom split normals to fix shading issues.  
* **Convert Empty to Collection**: Convert empty objects and their hierarchy into nested Collections. The empty object is deleted while its contents move to the new Collection.  
* **Auto Grouping**: Automatically organize objects into Collections based on their names.  
  * **Simple Mode**: Create a single-level Collection based on the first part of the name (e.g., `Hood_40` → `Hood`).  
  * **Complex Mode**: Create nested Collections based on name segments (e.g., `Rear_Spoiler_02` → `Spoiler` - `Rear`).  
* **Clean Empty Collections**: Remove all unused or empty Collections in the scene.

---

### 🎨 Material Operations
* **Merge Duplicate Materials**: Merge all materials sharing a similar suffix pattern (e.g., `.001`, `_001`, `-01`) into a single base material (e.g., `Material`). Only materials currently used in the scene are processed.  
* **Clean Unused Material Slots**: Remove unused material slots that are not assigned to any faces.  
* **Select Multi-Material Objects**: Select objects that contain more material slots than the defined threshold.

---

### 🚦 Export Preparation & Checking
* **Select Non-Uniform Scale**: Identify and select objects with scale values not equal to `1.0`.  
* **Rename by Collection**: Rename objects and their data blocks according to their Collection names (e.g., `Collection_001` → `Collection`).  
* **Add Triangulate Modifier**: Add triangulate modifiers to selected objects to preserve shading groups after export.  
* **Remove Triangulate Modifier**: Remove all triangulate modifiers from selected objects.

---

## 🧱 Version History

### 🆕 v1.2.1 New Features
* **Auto Grouping**: Organize objects into hierarchical Collections (Simple / Complex modes).  
* **Clean Empty Collections**: Remove all unused Collections in the scene.  
* **Clean Unused Material Slots**: Remove unassigned material slots from selected objects.  
* **Select Multi-Material Objects**: Filter objects that have more than the defined number of material slots.  
* **Merge Duplicate Materials**: Smart material merging using user-defined suffix patterns (e.g., `.001`, `_001`, `-01`).  

### 🆕 v1.2 New Features
* **Convert Empty to Collection**: Transform empty hierarchies into nested Collections.  
* **Merge Duplicate Materials**: Automatically remap and delete redundant materials.  

### 🧭 v1.1 New Features
* **Clear Custom Split Normals**: Quickly clear custom normal data from models.  
* **Select Multi-Material Objects**: Identify objects containing multiple material slots.  
* **Multi-Material Threshold**: Add control for minimum material slot count.  

### 🧰 v1.0 Base Features
* **Merge and Preserve Vertex Groups**: Combine multiple objects while retaining vertex groups for easy part selection.  
* **Select by Vertex Group Elements**: Quickly select face sets influenced by the active vertex group.  
* **Separate by Material**: Split multi-material objects into separate meshes by material.  
* **Clean Empty Vertex Groups**: Remove unused vertex groups to keep data clean.  
* **Select Non-Uniform Scale**: Identify objects with scales not equal to `1.0`.  
* **Rename by Collection**: Rename objects and data blocks using their Collection names to prevent export path errors.  
* **Add Triangulate Modifier**: Apply triangulate modifiers for consistent export surface smoothing.

---

## 💡 Usage Tips

* Always **save your project** before performing batch operations such as merging or cleanup.  
* Fully compatible with **Datasmith** pipelines.  
* Recommended for **Blender 4.0+** for complete feature support.

---

## 👨‍💻 Author

**Author:** CarlMarksWX  
🔗 GitHub: [CarlMarkswx/AutomotiveTools_for_blender](https://github.com/CarlMarkswx/AutomotiveTools_for_blender/)

---

> 🇨🇳 [返回中文版本 → README.md](./README.md)
